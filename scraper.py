"""Bienici property scraper using ScrapingAnt API."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from urllib.parse import urlencode

import requests

from config import (
    SCRAPINGANT_API_KEY,
    SCRAPINGANT_API_URL,
    SEARCH_URL,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    LOCATIONS,
    CONTRACT_TYPES,
    PROPERTY_TYPES,
)
from models import Property
from utils import (
    parse_total_count,
    parse_listings_from_page,
    parse_listing_urls,
    parse_property_detail,
)

logger = logging.getLogger(__name__)


class BieniciScraper:
    """Scraper for Bienici.com property listings.

    This scraper extracts property data from Bienici search pages
    and detail pages using the ScrapingAnt API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_workers: int = 5,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the scraper.

        Args:
            api_key: ScrapingAnt API key (uses env var if not provided)
            max_workers: Maximum parallel requests
            timeout: Request timeout in seconds

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or SCRAPINGANT_API_KEY
        if not self.api_key:
            raise ValueError(
                "ScrapingAnt API key is required. "
                "Set SCRAPINGANT_API_KEY environment variable or pass api_key parameter."
            )

        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()

    def _fetch_page(self, url: str, retries: int = MAX_RETRIES) -> Optional[str]:
        """Fetch a page using ScrapingAnt API.

        Args:
            url: URL to fetch
            retries: Number of retry attempts

        Returns:
            HTML content or None if failed
        """
        params = {
            "url": url,
            "x-api-key": self.api_key,
            "browser": "true",
            "proxy_country": "FR",
            "proxy_type": "residential",
        }

        for attempt in range(retries):
            try:
                response = self.session.get(
                    SCRAPINGANT_API_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{retries}): {e}"
                )
                if attempt < retries - 1:
                    wait_time = 2 ** attempt + 5
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    def _build_search_url(
        self,
        location: str,
        contract_type: str = "buy",
        property_type: str = "all",
        page: int = 1,
    ) -> str:
        """Build search URL with parameters.

        Args:
            location: City name or location code
            contract_type: buy, rent
            property_type: apartment, house, all, etc.
            page: Page number

        Returns:
            Full search URL
        """
        # Get location code
        location_code = LOCATIONS.get(location.lower(), location)

        # Get contract type in French
        contract = CONTRACT_TYPES.get(contract_type.lower(), "achat")

        # Build base URL
        # Pattern: /recherche/{contract}/{location}/{property_type}
        url_parts = [SEARCH_URL, contract, location_code]

        # Add property type if specified
        prop_type = PROPERTY_TYPES.get(property_type.lower(), "")
        if prop_type:
            url_parts.append(prop_type)

        url = "/".join(url_parts)

        # Add page parameter
        if page > 1:
            url += f"?page={page}"

        return url

    def scrape_page(
        self,
        location: str,
        contract_type: str = "buy",
        property_type: str = "all",
        page: int = 1,
    ) -> tuple:
        """Scrape a single search results page.

        Args:
            location: City name or location code
            contract_type: buy, rent
            property_type: apartment, house, all, etc.
            page: Page number

        Returns:
            Tuple of (total_count, list of property dictionaries)
        """
        url = self._build_search_url(location, contract_type, property_type, page)
        logger.debug(f"Fetching page {page}: {url}")

        html = self._fetch_page(url)
        if not html:
            return 0, []

        total_count = parse_total_count(html) if page == 1 else 0
        properties = parse_listings_from_page(html)

        return total_count, properties

    def scrape_detail(self, url: str) -> Optional[dict]:
        """Scrape a single property detail page.

        Args:
            url: Property detail URL

        Returns:
            Property dictionary or None if failed
        """
        logger.debug(f"Fetching detail: {url}")

        html = self._fetch_page(url)
        if not html:
            return None

        return parse_property_detail(html, url)

    def scrape(
        self,
        location: str,
        contract_type: str = "buy",
        property_type: str = "all",
        max_pages: Optional[int] = None,
        limit: Optional[int] = None,
        fetch_details: bool = True,
    ) -> List[Property]:
        """Scrape properties from Bienici.

        Args:
            location: City name or location code
            contract_type: buy, rent
            property_type: apartment, house, all, etc.
            max_pages: Maximum pages to scrape (None for all)
            limit: Maximum properties to scrape (None for all)
            fetch_details: Whether to fetch detail pages for more info

        Returns:
            List of Property objects
        """
        logger.info(
            f"Starting scrape: {property_type} for {contract_type} in {location}"
        )

        # Fetch first page to get total count
        url = self._build_search_url(location, contract_type, property_type, page=1)
        logger.info(f"Fetching first page: {url}")

        html = self._fetch_page(url)
        if not html:
            logger.warning("Failed to fetch first page")
            return []

        total_count = parse_total_count(html)
        first_page_properties = parse_listings_from_page(html)

        if not first_page_properties:
            logger.warning("No properties found on first page")
            return []

        # Estimate total pages (~24 listings per page on Bienici)
        listings_per_page = max(len(first_page_properties), 24)
        total_pages = (total_count + listings_per_page - 1) // listings_per_page

        logger.info(f"Found {total_count} properties across ~{total_pages} pages")

        # Determine pages to scrape
        pages_to_scrape = total_pages
        if max_pages:
            pages_to_scrape = min(pages_to_scrape, max_pages)

        logger.info(f"Will scrape {pages_to_scrape} pages")

        # Start with first page properties
        all_properties = first_page_properties

        # Fetch remaining pages in parallel
        if pages_to_scrape > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self.scrape_page,
                        location,
                        contract_type,
                        property_type,
                        page,
                    ): page
                    for page in range(2, pages_to_scrape + 1)
                }

                for future in as_completed(futures):
                    page = futures[future]
                    try:
                        _, page_properties = future.result()
                        all_properties.extend(page_properties)
                        logger.info(f"Page {page}: found {len(page_properties)} properties")
                    except Exception as e:
                        logger.error(f"Error fetching page {page}: {e}")

        # Remove duplicates by listing_id while preserving order
        seen = set()
        unique_properties = []
        for prop in all_properties:
            listing_id = prop.get("listing_id")
            if listing_id and listing_id not in seen:
                seen.add(listing_id)
                unique_properties.append(prop)

        # Apply limit
        if limit:
            unique_properties = unique_properties[:limit]

        logger.info(f"Collected {len(unique_properties)} unique properties")

        # Optionally fetch detail pages for more information
        if fetch_details:
            logger.info("Fetching detail pages...")
            unique_properties = self._enrich_with_details(unique_properties)

        # Convert to Property objects
        properties = []
        for prop_dict in unique_properties:
            try:
                properties.append(Property(**prop_dict))
            except Exception as e:
                logger.warning(f"Failed to create Property: {e}")

        logger.info(f"Successfully scraped {len(properties)} properties")
        return properties

    def _enrich_with_details(self, properties: List[dict]) -> List[dict]:
        """Fetch detail pages to enrich property data.

        Args:
            properties: List of property dictionaries

        Returns:
            Enriched property dictionaries
        """
        urls = [p.get("url") for p in properties if p.get("url")]

        if not urls:
            return properties

        # Create URL to property mapping
        prop_by_url = {p.get("url"): p for p in properties}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.scrape_detail, url): url
                for url in urls
            }

            for future in as_completed(futures):
                url = futures[future]
                try:
                    detail = future.result()
                    if detail and url in prop_by_url:
                        # Merge detail data into existing property
                        # Preserve data from list page, add from detail
                        merged = prop_by_url[url].copy()
                        for key, value in detail.items():
                            if value and (not merged.get(key) or key in [
                                "description", "agency_name", "agency_address",
                                "energy_rating", "ges_rating", "floor", "exposure",
                                "heating_type", "published_date", "modified_date",
                                "reference", "mandate_type", "energy_consumption",
                                "ges_emission", "energy_bill_min", "energy_bill_max",
                                "price_without_fees", "agency_fees_percent"
                            ]):
                                merged[key] = value
                        prop_by_url[url] = merged
                except Exception as e:
                    logger.warning(f"Error fetching detail {url}: {e}")

        return list(prop_by_url.values())
