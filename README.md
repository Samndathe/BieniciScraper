# Bienici.com Scraper

A Python scraper for extracting property listings from [Bienici.com](https://www.bienici.com) (France's largest real estate portal) using the ScrapingAnt API.

## Features

- Scrapes apartments, houses, land, and other property types
- Supports buy and rent listings
- Covers all major French cities (Paris, Lyon, Marseille, etc.)
- Parallel scraping for improved performance
- Extracts 25+ property attributes including price, area, rooms, location, energy ratings
- Fetches detailed property pages for complete information
- Exports data to CSV format
- Rate limiting and retry logic for reliability

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kami4ka/BieniciScraper.git
cd BieniciScraper
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Scrape apartments for sale in Paris
python main.py --location paris --property apartment

# Scrape houses for rent in Lyon
python main.py --location lyon --contract rent --property house

# Scrape with page limit
python main.py --location marseille --max-pages 5

# Scrape with property limit
python main.py --location toulouse --limit 100

# Fast scrape without detail pages
python main.py --location nice --max-pages 3 --no-details

# Enable verbose logging
python main.py --location bordeaux --max-pages 3 -v
```

### Available Options

| Option | Description |
|--------|-------------|
| `--location`, `-l` | Location to search (default: paris) |
| `--contract`, `-c` | Contract type: buy, rent (default: buy) |
| `--property`, `-p` | Property type (default: all) |
| `--output`, `-o` | Output CSV file path (default: properties.csv) |
| `--limit` | Maximum number of properties to scrape |
| `--max-pages` | Maximum number of listing pages to scrape |
| `--max-workers`, `-w` | Maximum parallel requests (default: 10) |
| `--no-details` | Skip fetching detail pages (faster but less data) |
| `--api-key`, `-k` | ScrapingAnt API key (overrides environment variable) |
| `--verbose`, `-v` | Enable verbose logging |

### Contract Types

| Type | Description |
|------|-------------|
| `buy` | Properties for sale (Achat) |
| `rent` | Properties for rent (Location) |

### Property Types

| Type | Description |
|------|-------------|
| `all` | All properties |
| `apartment` | Apartments |
| `house` | Houses and villas |
| `land` | Land/Plots |
| `parking` | Parking spaces |
| `commercial` | Commercial properties |
| `office` | Office spaces |

### Location Examples

- `paris` - Paris
- `lyon` - Lyon
- `marseille` - Marseille
- `toulouse` - Toulouse
- `nice` - Nice
- `nantes` - Nantes
- `montpellier` - Montpellier
- `strasbourg` - Strasbourg
- `bordeaux` - Bordeaux
- `lille` - Lille

## Output Format

The scraper exports data to CSV with the following fields:

| Field | Description |
|-------|-------------|
| url | Property listing URL |
| listing_id | Unique listing identifier |
| title | Property title |
| property_type | Type (apartment, house, etc.) |
| contract_type | Buy or Rent |
| price | Listed price in EUR |
| price_per_sqm | Price per square meter |
| price_without_fees | Price excluding agency fees |
| agency_fees_percent | Agency fees percentage |
| city | City name |
| district | District/neighborhood name |
| postal_code | Postal code |
| full_address | Full address |
| living_area | Living area in m² |
| rooms | Number of rooms |
| bedrooms | Number of bedrooms |
| floor | Floor number |
| exposure | Property exposure (N, S, E, W) |
| heating_type | Heating type and mode |
| energy_rating | Energy certificate class (A-G) |
| energy_consumption | Energy consumption kWh/m²/year |
| ges_rating | GES emissions class (A-G) |
| ges_emission | GES emission kgCO₂/m²/year |
| energy_bill_min | Minimum estimated energy bill |
| energy_bill_max | Maximum estimated energy bill |
| has_video | Has video tour |
| is_exclusive | Exclusive listing |
| price_drop | Recent price drop |
| agency_name | Agency name |
| agency_address | Agency address |
| mandate_type | Mandate type (exclusive, etc.) |
| reference | Listing reference number |
| description | Property description |
| published_date | Publication date |
| modified_date | Last modification date |
| date_scraped | Scraping timestamp |

## API Configuration

This scraper uses the [ScrapingAnt API](https://scrapingant.com) for web scraping. You can provide the API key via:

1. Environment variable: `export SCRAPINGANT_API_KEY=your_key`
2. Command line: `--api-key YOUR_KEY`

Configuration options in `config.py`:

- `SCRAPINGANT_API_KEY`: Your API key
- `DEFAULT_MAX_WORKERS`: Parallel request limit (default: 10)
- `DEFAULT_TIMEOUT`: Request timeout in seconds (default: 120)
- `MAX_RETRIES`: Number of retry attempts (default: 3)

## License

MIT License
