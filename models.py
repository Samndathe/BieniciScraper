"""Data models for Bienici scraper."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Property:
    """Represents a property listing from Bienici."""

    # Basic information
    url: str = ""
    listing_id: str = ""
    title: str = ""

    # Property details
    property_type: str = ""
    contract_type: str = ""

    # Pricing
    price: Optional[int] = None
    price_per_sqm: Optional[float] = None
    price_without_fees: Optional[int] = None
    agency_fees_percent: Optional[float] = None

    # Location
    city: str = ""
    district: str = ""
    postal_code: str = ""
    full_address: str = ""

    # Property characteristics
    living_area: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None

    # Building info
    floor: str = ""
    exposure: str = ""

    # Heating
    heating_type: str = ""

    # Energy
    energy_rating: str = ""
    energy_consumption: Optional[int] = None
    ges_rating: str = ""
    ges_emission: Optional[int] = None
    energy_bill_min: Optional[int] = None
    energy_bill_max: Optional[int] = None

    # Tags/Features
    has_video: bool = False
    is_exclusive: bool = False
    price_drop: bool = False

    # Seller information
    agency_name: str = ""
    agency_address: str = ""
    mandate_type: str = ""
    reference: str = ""

    # Description
    description: str = ""

    # Metadata
    published_date: str = ""
    modified_date: str = ""
    date_scraped: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return asdict(self)
