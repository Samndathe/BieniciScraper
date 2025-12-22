"""Utility functions for Bienici scraper."""

import re
import json
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from config import BASE_URL

logger = logging.getLogger(__name__)


def parse_total_count(html: str) -> int:
    """Extract total number of listings from search page.

    Args:
        html: HTML content of search page

    Returns:
        Total count of listings
    """
    soup = BeautifulSoup(html, "lxml")

    # Look for heading with count pattern "X biens à vendre"
    headings = soup.find_all("h2")
    for h2 in headings:
        text = h2.get_text(strip=True)
        match = re.search(r"([\d\s\xa0]+)\s*biens?\s+(?:à\s+vendre|à\s+louer)", text)
        if match:
            count_str = match.group(1).replace(" ", "").replace("\xa0", "")
            try:
                return int(count_str)
            except ValueError:
                pass

    return 0


def parse_listing_urls(html: str) -> List[str]:
    """Extract property listing URLs from search page.

    Args:
        html: HTML content of search page

    Returns:
        List of property detail URLs
    """
    soup = BeautifulSoup(html, "lxml")
    urls = []

    # Find all article elements with links to property details
    articles = soup.find_all("article")
    for article in articles:
        link = article.find("a", href=re.compile(r"/annonce/"))
        if link and link.get("href"):
            href = link["href"]
            # Remove query string parameters
            href = href.split("?")[0]
            if href.startswith("/"):
                href = BASE_URL + href
            if href not in urls:
                urls.append(href)

    return urls


def parse_listings_from_page(html: str) -> List[Dict[str, Any]]:
    """Extract listing data from search page cards.

    Args:
        html: HTML content of search page

    Returns:
        List of property dictionaries with basic info from cards
    """
    soup = BeautifulSoup(html, "lxml")
    properties = []

    articles = soup.find_all("article")
    for article in articles:
        try:
            prop = extract_listing_card_data(article)
            if prop and prop.get("url"):
                properties.append(prop)
        except Exception as e:
            logger.warning(f"Failed to parse listing card: {e}")

    return properties


def extract_listing_card_data(article) -> Optional[Dict[str, Any]]:
    """Extract data from a single listing card.

    Args:
        article: BeautifulSoup element for the article

    Returns:
        Dictionary with property data or None
    """
    prop = {}

    # Get URL and listing ID
    link = article.find("a", href=re.compile(r"/annonce/"))
    if not link:
        return None

    href = link.get("href", "")
    href = href.split("?")[0]
    if href.startswith("/"):
        prop["url"] = BASE_URL + href
    else:
        prop["url"] = href

    # Extract listing ID from URL
    # URL pattern: /annonce/vente/city/type/pieces/listing_id
    parts = href.rstrip("/").split("/")
    if parts:
        prop["listing_id"] = parts[-1]

    # Get title (property type, rooms, area)
    h3 = article.find("h3")
    if h3:
        title_text = h3.get_text(strip=True)
        prop["title"] = title_text

        # Parse property type, rooms, area from title
        # Example: "Appartement 3 pièces 78 m² 75018 Paris 18e"
        prop.update(parse_title_text(title_text))

    # Get price
    price_elem = article.find(string=re.compile(r"[\d\s]+\s*€"))
    if price_elem:
        price_text = price_elem.strip()
        prop["price"] = parse_price(price_text)

    # Alternative: look for price in nested divs
    if not prop.get("price"):
        for div in article.find_all("div"):
            text = div.get_text(strip=True)
            if "€" in text and re.search(r"\d", text):
                price = parse_price(text)
                if price and price > 1000:
                    prop["price"] = price
                    break

    # Get price per sqm
    price_per_sqm_match = article.find(string=re.compile(r"[\d\s,]+\s*€/m²"))
    if price_per_sqm_match:
        prop["price_per_sqm"] = parse_price_per_sqm(price_per_sqm_match.strip())

    # Check for tags
    text = article.get_text()
    prop["has_video"] = "Vidéo" in text
    prop["is_exclusive"] = "Exclusivité" in text
    prop["price_drop"] = "Baisse de prix" in text

    # Determine contract type from URL
    if "/vente/" in href:
        prop["contract_type"] = "buy"
    elif "/location/" in href:
        prop["contract_type"] = "rent"

    return prop


def parse_title_text(title: str) -> Dict[str, Any]:
    """Parse property type, rooms, and area from title.

    Args:
        title: Title text like "Appartement 3 pièces 78 m²"

    Returns:
        Dictionary with parsed values
    """
    result = {}

    # Extract property type
    property_types = {
        "appartement": "apartment",
        "maison": "house",
        "studio": "studio",
        "duplex": "duplex",
        "loft": "loft",
        "terrain": "land",
        "parking": "parking",
        "commerce": "commercial",
        "bureaux": "office",
        "villa": "house",
        "immeuble": "building",
    }

    title_lower = title.lower()
    for fr_type, en_type in property_types.items():
        if fr_type in title_lower:
            result["property_type"] = en_type
            break

    # Extract rooms count
    rooms_match = re.search(r"(\d+)\s*pièces?", title)
    if rooms_match:
        result["rooms"] = int(rooms_match.group(1))

    # Extract area
    area_match = re.search(r"(\d+(?:[,\.]\d+)?)\s*m²", title)
    if area_match:
        area_str = area_match.group(1).replace(",", ".")
        result["living_area"] = float(area_str)

    # Extract postal code and city
    postal_match = re.search(r"(\d{5})\s+([^(]+?)(?:\s*\(|$)", title)
    if postal_match:
        result["postal_code"] = postal_match.group(1)
        result["city"] = postal_match.group(2).strip()

    # Extract district (in parentheses)
    district_match = re.search(r"\(([^)]+)\)", title)
    if district_match:
        result["district"] = district_match.group(1)

    return result


def parse_property_detail(html: str, url: str) -> Dict[str, Any]:
    """Parse property details from detail page.

    Args:
        html: HTML content of detail page
        url: URL of the property

    Returns:
        Dictionary with all property details
    """
    soup = BeautifulSoup(html, "lxml")
    prop = {"url": url}

    # Extract listing ID from URL
    parts = url.rstrip("/").split("/")
    prop["listing_id"] = parts[-1].split("?")[0] if parts else ""

    # Get title
    h1 = soup.find("h1")
    if h1:
        prop["title"] = h1.get_text(strip=True)
        prop.update(parse_title_text(prop["title"]))

    # Get full page text for searching
    page_text = soup.get_text()

    # Parse price
    price_match = re.search(r"(\d[\d\s\xa0]*)\s*€(?!\s*/\s*m)", page_text)
    if price_match:
        prop["price"] = parse_price(price_match.group(0))

    # Parse price per sqm
    price_per_sqm_match = re.search(r"(\d[\d\s\xa0,]*)\s*€\s*/\s*m²", page_text)
    if price_per_sqm_match:
        prop["price_per_sqm"] = parse_price_per_sqm(price_per_sqm_match.group(0))

    # Parse agency fees
    fees_match = re.search(r"Honoraires\s*:\s*([\d,\.]+)\s*%", page_text)
    if fees_match:
        prop["agency_fees_percent"] = float(fees_match.group(1).replace(",", "."))

    # Parse price without fees
    price_hors_match = re.search(r"\(([\d\s\xa0]+)\s*€\s*hors\s*honoraires\)", page_text)
    if price_hors_match:
        prop["price_without_fees"] = parse_price(price_hors_match.group(1))

    # Parse floor
    floor_match = re.search(r"(\d+)(?:er|ème|e)?\s*étage|Rez-de-chaussée", page_text)
    if floor_match:
        if "Rez-de-chaussée" in floor_match.group(0):
            prop["floor"] = "0"
        else:
            prop["floor"] = floor_match.group(1)

    # Parse exposure
    exposure_match = re.search(r"Exposé?\s+([\w\s]+?)(?:\n|$|\.)", page_text)
    if exposure_match:
        prop["exposure"] = exposure_match.group(1).strip()

    # Parse heating
    heating_match = re.search(r"Chauffage\s*:\s*([^\.]+?)(?:\n|$|\.)", page_text)
    if heating_match:
        prop["heating_type"] = heating_match.group(1).strip()

    # Parse DPE date
    dpe_date_match = re.search(r"Date de réalisation du DPE\s*:\s*(\d+\s+\w+\s+\d+)", page_text)
    if dpe_date_match:
        prop["dpe_date"] = dpe_date_match.group(1)

    # Parse energy rating
    # Look for energy class A-G
    energy_section = soup.find(string=re.compile(r"Performance énergétique"))
    if energy_section:
        parent = energy_section.find_parent()
        if parent:
            section_text = parent.get_text()
            rating_match = re.search(r"\b([A-G])\b.*?(\d+)\s*kWh", section_text, re.DOTALL)
            if rating_match:
                prop["energy_rating"] = rating_match.group(1)
                prop["energy_consumption"] = int(rating_match.group(2))

    # Alternative energy rating parsing
    if not prop.get("energy_rating"):
        for elem in soup.find_all(string=re.compile(r"^\s*[A-G]\s*$")):
            parent = elem.find_parent()
            if parent and "dpe" in str(parent.get("class", [])).lower():
                prop["energy_rating"] = elem.strip()
                break

    # Parse GES rating
    ges_match = re.search(r"émissions.*?([A-G])\s*(\d+)\s*kg\s*CO", page_text, re.IGNORECASE | re.DOTALL)
    if ges_match:
        prop["ges_rating"] = ges_match.group(1)
        prop["ges_emission"] = int(ges_match.group(2))

    # Parse energy bill estimate
    bill_match = re.search(r"Entre\s*([\d\s]+)\s*€\s*et\s*([\d\s]+)\s*€\s*par\s*an", page_text)
    if bill_match:
        prop["energy_bill_min"] = parse_price(bill_match.group(1))
        prop["energy_bill_max"] = parse_price(bill_match.group(2))

    # Parse mandate type
    if "exclusivité" in page_text.lower():
        prop["mandate_type"] = "exclusive"

    # Parse reference
    ref_match = re.search(r"Réf\.\s*(?:de l'annonce\s*)?:\s*(\S+)", page_text)
    if ref_match:
        prop["reference"] = ref_match.group(1)

    # Parse dates
    pub_match = re.search(r"Publiée?\s+le\s+(\d+\s+\w+\.?\s+\d+)", page_text)
    if pub_match:
        prop["published_date"] = pub_match.group(1)

    mod_match = re.search(r"Modifiée?\s+le\s+(\d+\s+\w+\.?\s+\d+)", page_text)
    if mod_match:
        prop["modified_date"] = mod_match.group(1)

    # Parse agency info
    agency_section = soup.find(string=re.compile(r"À propos de l'agence"))
    if agency_section:
        parent = agency_section.find_parent()
        if parent:
            h1_agency = parent.find("h1")
            if h1_agency:
                prop["agency_name"] = h1_agency.get_text(strip=True)
            # Look for address
            for elem in parent.find_all(["div", "span", "p"]):
                text = elem.get_text(strip=True)
                if re.search(r"\d{5}", text) and len(text) < 100:
                    prop["agency_address"] = text
                    break

    # Parse description
    desc_section = soup.find(string=re.compile(r"Descriptif de ce"))
    if desc_section:
        parent = desc_section.find_parent()
        if parent:
            desc_div = parent.find_next_sibling() or parent.find_parent()
            if desc_div:
                prop["description"] = desc_div.get_text(strip=True)[:2000]

    # Check for tags
    prop["has_video"] = "Vidéo" in page_text
    prop["is_exclusive"] = "Exclusivité" in page_text
    prop["price_drop"] = "Baisse de prix" in page_text

    # Determine contract type from URL
    if "/vente/" in url:
        prop["contract_type"] = "buy"
    elif "/location/" in url:
        prop["contract_type"] = "rent"

    return prop


def parse_price(text: str) -> Optional[int]:
    """Parse price from text.

    Args:
        text: Text containing price like "430 000 €"

    Returns:
        Price as integer or None
    """
    if not text:
        return None

    # Remove non-numeric characters except digits
    clean = re.sub(r"[^\d]", "", text)
    if clean:
        try:
            return int(clean)
        except ValueError:
            pass
    return None


def parse_price_per_sqm(text: str) -> Optional[float]:
    """Parse price per square meter from text.

    Args:
        text: Text containing price like "9 055 €/m²" or "12,2k €/m²"

    Returns:
        Price per sqm as float or None
    """
    if not text:
        return None

    # Handle "k" notation (e.g., "12,2k €/m²")
    k_match = re.search(r"([\d,\.]+)\s*k", text.lower())
    if k_match:
        value = k_match.group(1).replace(",", ".")
        try:
            return float(value) * 1000
        except ValueError:
            pass

    # Standard number
    num_match = re.search(r"([\d\s\xa0]+)", text)
    if num_match:
        clean = re.sub(r"[^\d]", "", num_match.group(1))
        if clean:
            try:
                return float(clean)
            except ValueError:
                pass

    return None


def check_for_next_data(html: str) -> Optional[Dict]:
    """Check for embedded JSON data in __NEXT_DATA__ script tag.

    Args:
        html: HTML content

    Returns:
        Parsed JSON data or None
    """
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass
    return None
