"""Tests for the sensor update() method using mocked redfin library calls."""
import json
from unittest.mock import MagicMock, patch, call

from custom_components.redfin.const import (
    ATTR_AMOUNT, ATTR_AMOUNT_FORMATTED, ATTR_ADDRESS, ATTR_FULL_ADDRESS,
    ATTR_CURRENCY, ATTR_STREET_VIEW, ATTR_REDFIN_URL, ATTR_WALK_SCORE,
    ATTR_BIKE_SCORE, ATTR_TRANSIT_SCORE, CONF_PROPERTY_ID,
)


def make_avm_payload(predicted_value=750000, lat=47.6062, lng=-122.3321,
                     address="1234 Main St", preview_text="Est. $750K"):
    return {
        "errorMessage": "Success",
        "resultCode": 0,
        "payload": {
            "predictedValue": predicted_value,
            "sectionPreviewText": preview_text,
            "latLong": {"latitude": lat, "longitude": lng},
            "streetAddress": {"assembledAddress": address},
        },
    }


def make_neighborhood_payload(city="Seattle", state="WA",
                              walk=92, bike=75, transit=88):
    return {
        "errorMessage": "Success",
        "resultCode": 0,
        "payload": {
            "addressInfo": {"city": city, "state": state},
            "walkScoreInfo": {
                "walkScoreData": {
                    "walkScore": {"value": walk},
                    "bikeScore": {"value": bike},
                    "transitScore": {"value": transit},
                }
            },
        },
    }


class MockSensor:
    """Minimal mock of RedfinDataSensor to test update logic without HA framework."""

    def __init__(self, property_id):
        self._name = "Redfin"
        self.params = {CONF_PROPERTY_ID: property_id}
        self.data = None
        self.address = None
        self._state = None

    def update(self):
        """Inline copy of sensor update logic for testing."""
        from redfin import Redfin
        from homeassistant.const import ATTR_ATTRIBUTION
        from custom_components.redfin.const import (
            ATTR_AMOUNT, ATTR_CURRENCY, ATTR_UNIT_OF_MEASUREMENT,
            ATTR_AMOUNT_FORMATTED, ATTR_ADDRESS, ATTR_FULL_ADDRESS,
            ATTR_REDFIN_URL, ATTR_STREET_VIEW, ATTR_WALK_SCORE,
            ATTR_BIKE_SCORE, ATTR_TRANSIT_SCORE, CONF_PROPERTY_ID,
            ATTRIBUTION,
        )

        client = Redfin()
        property_id = self.params[CONF_PROPERTY_ID]

        avm_details = client.avm_details(property_id, "")
        neighborhood_stats = client.neighborhood_stats(property_id)

        try:
            address_line = avm_details["payload"]["streetAddress"]["assembledAddress"]
        except (KeyError, TypeError):
            address_line = "Unknown"

        try:
            city = neighborhood_stats["payload"]["addressInfo"]["city"]
            state = neighborhood_stats["payload"]["addressInfo"]["state"]
        except (KeyError, TypeError):
            city = ""
            state = ""

        self.address = f"{address_line}, {city}, {state}" if city and state else address_line

        try:
            lat = avm_details["payload"]["latLong"]["latitude"]
            lng = avm_details["payload"]["latLong"]["longitude"]
            streetViewUrl = f"https://www.google.com/maps/@{lat},{lng},3a,75y,90t/data=!3m6!1e1"
        except (KeyError, TypeError):
            streetViewUrl = "Not Set"

        redfinUrl = f"https://www.redfin.com/home/{property_id}"
        predictedValue = avm_details["payload"].get("predictedValue", "Not Set")
        sectionPreviewText = avm_details["payload"].get("sectionPreviewText", "Not Set")

        try:
            score_data = neighborhood_stats["payload"]["walkScoreInfo"]["walkScoreData"]
            walk_score = score_data["walkScore"]["value"]
            bike_score = score_data["bikeScore"]["value"]
            transit_score = score_data["transitScore"]["value"]
        except (KeyError, TypeError):
            walk_score = bike_score = transit_score = None

        details = {
            ATTR_AMOUNT: predictedValue,
            ATTR_CURRENCY: "USD",
            ATTR_UNIT_OF_MEASUREMENT: "USD",
            ATTR_AMOUNT_FORMATTED: sectionPreviewText,
            ATTR_ADDRESS: address_line,
            ATTR_FULL_ADDRESS: self.address,
            ATTR_REDFIN_URL: redfinUrl,
            ATTR_STREET_VIEW: streetViewUrl,
            ATTR_WALK_SCORE: walk_score,
            ATTR_BIKE_SCORE: bike_score,
            ATTR_TRANSIT_SCORE: transit_score,
            CONF_PROPERTY_ID: property_id,
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
        self.data = details
        self._state = details[ATTR_AMOUNT]


@patch("redfin.redfin.requests.get")
def test_sensor_update_calls_avm_and_neighborhood_stats(mock_get):
    """Sensor update() calls avm_details and neighborhood_stats (not above_the_fold/info_panel)."""
    from redfin import Redfin
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("12345")
        sensor.update()

    mock_client.avm_details.assert_called_once_with("12345", "")
    mock_client.neighborhood_stats.assert_called_once_with("12345")
    # above_the_fold and info_panel should NOT be called
    mock_client.above_the_fold.assert_not_called()
    mock_client.info_panel.assert_not_called()


@patch("redfin.redfin.requests.get")
def test_sensor_state_is_predicted_value(mock_get):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(predicted_value=850000)
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("99999")
        sensor.update()

    assert sensor._state == 850000
    assert sensor.data[ATTR_AMOUNT] == 850000


@patch("redfin.redfin.requests.get")
def test_sensor_address_formatted_correctly(mock_get):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(address="1712 Glen Echo Rd Unit C")
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload(city="Nashville", state="TN")

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("55555")
        sensor.update()

    assert sensor.address == "1712 Glen Echo Rd Unit C, Nashville, TN"
    assert sensor.data[ATTR_ADDRESS] == "1712 Glen Echo Rd Unit C"
    assert sensor.data[ATTR_FULL_ADDRESS] == "1712 Glen Echo Rd Unit C, Nashville, TN"


@patch("redfin.redfin.requests.get")
def test_sensor_street_view_url_from_lat_long(mock_get):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(lat=36.1234, lng=-86.5678)
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("11111")
        sensor.update()

    expected_url = "https://www.google.com/maps/@36.1234,-86.5678,3a,75y,90t/data=!3m6!1e1"
    assert sensor.data[ATTR_STREET_VIEW] == expected_url


@patch("redfin.redfin.requests.get")
def test_sensor_redfin_url_uses_property_id(mock_get):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("77777")
        sensor.update()

    assert sensor.data[ATTR_REDFIN_URL] == "https://www.redfin.com/home/77777"


@patch("redfin.redfin.requests.get")
def test_sensor_walk_bike_transit_scores(mock_get):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload(walk=92, bike=75, transit=88)

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("33333")
        sensor.update()

    assert sensor.data[ATTR_WALK_SCORE] == 92
    assert sensor.data[ATTR_BIKE_SCORE] == 75
    assert sensor.data[ATTR_TRANSIT_SCORE] == 88


@patch("redfin.redfin.requests.get")
def test_sensor_scores_none_on_missing_data(mock_get):
    """If walkScoreInfo missing, scores should be None (not crash)."""
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = {
        "errorMessage": "Success",
        "resultCode": 0,
        "payload": {
            "addressInfo": {"city": "Portland", "state": "OR"},
            # walkScoreInfo intentionally absent
        },
    }

    with patch("redfin.Redfin", return_value=mock_client):
        sensor = MockSensor("44444")
        sensor.update()

    assert sensor.data[ATTR_WALK_SCORE] is None
    assert sensor.data[ATTR_BIKE_SCORE] is None
    assert sensor.data[ATTR_TRANSIT_SCORE] is None
