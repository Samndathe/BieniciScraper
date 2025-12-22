#!/usr/bin/env python3
"""Main entry point for Bienici scraper."""

import argparse
import csv
import logging
import sys
from typing import List

from scraper import BieniciScraper
from models import Property
from config import LOCATIONS, CONTRACT_TYPES, PROPERTY_TYPES, DEFAULT_MAX_WORKERS


def setup_logging(verbose: bool = False) -> None:
    """Configure logging settings."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def export_to_csv(properties: List[Property], output_path: str) -> None:
    """Export properties to CSV file.

    Args:
        properties: List of Property objects
        output_path: Path to output CSV file
    """
    if not properties:
        logging.warning("No properties to export")
        return

    fieldnames = list(properties[0].to_dict().keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for prop in properties:
            writer.writerow(prop.to_dict())

    logging.info(f"Exported {len(properties)} properties to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape property listings from Bienici.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --location paris --property apartment
  %(prog)s --location lyon --contract rent --property house
  %(prog)s --location marseille --max-pages 5
  %(prog)s --location toulouse --limit 100
  %(prog)s --location nice --max-pages 3 -v
        """,
    )

    parser.add_argument(
        "--location", "-l",
        default="paris",
        help=f"Location to search. Available: {', '.join(LOCATIONS.keys())} (default: paris)",
    )
    parser.add_argument(
        "--contract", "-c",
        choices=list(CONTRACT_TYPES.keys()),
        default="buy",
        help="Contract type (default: buy)",
    )
    parser.add_argument(
        "--property", "-p",
        choices=list(PROPERTY_TYPES.keys()),
        default="all",
        help="Property type (default: all)",
    )
    parser.add_argument(
        "--output", "-o",
        default="properties.csv",
        help="Output CSV file path (default: properties.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of properties to scrape",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum number of listing pages to scrape",
    )
    parser.add_argument(
        "--max-workers", "-w",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Maximum parallel requests (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Skip fetching detail pages (faster but less data)",
    )
    parser.add_argument(
        "--api-key", "-k",
        help="ScrapingAnt API key (overrides environment variable)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        scraper = BieniciScraper(
            api_key=args.api_key,
            max_workers=args.max_workers,
        )

        properties = scraper.scrape(
            location=args.location,
            contract_type=args.contract,
            property_type=args.property,
            max_pages=args.max_pages,
            limit=args.limit,
            fetch_details=not args.no_details,
        )

        if properties:
            export_to_csv(properties, args.output)
            logger.info(f"Successfully scraped {len(properties)} properties")
        else:
            logger.warning("No properties found")
            sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
