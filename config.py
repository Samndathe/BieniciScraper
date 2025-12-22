"""Configuration for Bienici scraper."""

import os

# ScrapingAnt API Configuration
SCRAPINGANT_API_KEY = os.getenv("SCRAPINGANT_API_KEY", "")
SCRAPINGANT_API_URL = "https://api.scrapingant.com/v2/general"

# Bienici URLs
BASE_URL = "https://www.bienici.com"
SEARCH_URL = "https://www.bienici.com/recherche"

# Request Configuration
DEFAULT_TIMEOUT = 120
MAX_RETRIES = 3
DEFAULT_MAX_WORKERS = 10

# Location codes for major French cities
LOCATIONS = {
    "paris": "paris-75000",
    "lyon": "lyon-69000",
    "marseille": "marseille-13000",
    "toulouse": "toulouse-31000",
    "nice": "nice-06000",
    "nantes": "nantes-44000",
    "montpellier": "montpellier-34000",
    "strasbourg": "strasbourg-67000",
    "bordeaux": "bordeaux-33000",
    "lille": "lille-59000",
    "rennes": "rennes-35000",
    "reims": "reims-51100",
    "saint-etienne": "saint-etienne-42000",
    "le-havre": "le-havre-76600",
    "toulon": "toulon-83000",
    "grenoble": "grenoble-38000",
    "dijon": "dijon-21000",
    "angers": "angers-49000",
    "nimes": "nimes-30000",
    "aix-en-provence": "aix-en-provence-13100",
}

# Contract types
CONTRACT_TYPES = {
    "buy": "achat",
    "rent": "location",
    "new": "achat",  # with neuf=oui parameter
}

# Property types
PROPERTY_TYPES = {
    "all": "",
    "apartment": "appartement",
    "house": "maisonvilla",
    "land": "terrain",
    "parking": "parking",
    "commercial": "commerce",
    "office": "bureaux",
}

# CSS Selectors for parsing
SELECTORS = {
    # List page selectors
    "total_count": "h2",  # Contains "X biens à vendre"
    "listing_card": "article",
    "listing_link": "article a[href*='/annonce/']",
    "pagination_link": "a[href*='page=']",

    # Detail page selectors
    "title": "h1",
    "price": "[class*='price'], [class*='Price']",
    "price_per_sqm": "[class*='pricePerSquareMeter'], [class*='price-per']",
    "description": "[class*='description'], [class*='Description']",
    "features": "[class*='features'], [class*='Features'], [class*='about']",
    "agency_name": "[class*='agency'], [class*='Agency']",
    "energy_rating": "[class*='dpe'], [class*='energy']",
}
