DOMAIN = "redfin"

DEFAULT_NAME = "Redfin"

ATTRIBUTION = "Data provided by Redfin.com"
RESOURCE_URL = "https://www.redfin.com"

# API endpoints (direct — no PyPI library needed)
AVM_URL = "https://www.redfin.com/stingray/api/home/details/avm"
NEIGHBORHOOD_STATS_URL = (
    "https://www.redfin.com/stingray/api/home/details/neighborhoodStats/statsInfo"
)

ATTR_AMOUNT = "amount"
ATTR_AMOUNT_FORMATTED = "amount_formatted"
ATTR_ADDRESS = "address"
ATTR_FULL_ADDRESS = "full_address"
ATTR_CURRENCY = "amount_currency"
ATTR_STREET_VIEW = "street_view"
ATTR_REDFIN_URL = "redfin_url"
ATTR_UNIT_OF_MEASUREMENT = "unit_of_measurement"
ATTR_BEDROOMS = "bedrooms"
ATTR_BATHROOMS = "bathrooms"
ATTR_SQUARE_FEET = "square_feet"
ATTR_WALK_SCORE = "walk_score"
ATTR_BIKE_SCORE = "bike_score"
ATTR_TRANSIT_SCORE = "transit_score"

CONF_PROPERTIES = "properties"
CONF_PROPERTY_ID = "property_id"
CONF_PROPERTY_IDS = "property_ids"
DEFAULT_SCAN_INTERVAL = 60
CONF_SCAN_INTERVAL_MIN = 5
CONF_SCAN_INTERVAL_MAX = 600

ICON = "mdi:home-variant"

# Required headers to avoid CloudFront 403
REDFIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
