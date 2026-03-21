"""Tests for the sensor update() method using mocked redfin library calls."""
from unittest.mock import MagicMock, patch

from custom_components.redfin.sensor import RedfinDataSensor
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


def make_sensor(property_id="12345"):
    params = {CONF_PROPERTY_ID: property_id}
    return RedfinDataSensor("Redfin", params, 60)


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_update_calls_avm_and_neighborhood_stats(MockRedfin):
    """Sensor update() calls avm_details and neighborhood_stats (not above_the_fold/info_panel)."""
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()
    MockRedfin.return_value = mock_client

    sensor = make_sensor("12345")
    sensor.update()

    mock_client.avm_details.assert_called_once_with("12345", "")
    mock_client.neighborhood_stats.assert_called_once_with("12345")
    mock_client.above_the_fold.assert_not_called()
    mock_client.info_panel.assert_not_called()


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_state_is_predicted_value(MockRedfin):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(predicted_value=850000)
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()
    MockRedfin.return_value = mock_client

    sensor = make_sensor("99999")
    sensor.update()

    assert sensor._state == 850000
    assert sensor.data[ATTR_AMOUNT] == 850000


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_address_formatted_correctly(MockRedfin):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(address="1712 Glen Echo Rd Unit C")
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload(city="Nashville", state="TN")
    MockRedfin.return_value = mock_client

    sensor = make_sensor("55555")
    sensor.update()

    assert sensor.address == "1712 Glen Echo Rd Unit C, Nashville, TN"
    assert sensor.data[ATTR_ADDRESS] == "1712 Glen Echo Rd Unit C"
    assert sensor.data[ATTR_FULL_ADDRESS] == "1712 Glen Echo Rd Unit C, Nashville, TN"


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_street_view_url_from_lat_long(MockRedfin):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload(lat=36.1234, lng=-86.5678)
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()
    MockRedfin.return_value = mock_client

    sensor = make_sensor("11111")
    sensor.update()

    expected_url = "https://www.google.com/maps/@36.1234,-86.5678,3a,75y,90t/data=!3m6!1e1"
    assert sensor.data[ATTR_STREET_VIEW] == expected_url


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_redfin_url_uses_property_id(MockRedfin):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload()
    MockRedfin.return_value = mock_client

    sensor = make_sensor("77777")
    sensor.update()

    assert sensor.data[ATTR_REDFIN_URL] == "https://www.redfin.com/home/77777"


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_walk_bike_transit_scores(MockRedfin):
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_payload()
    mock_client.neighborhood_stats.return_value = make_neighborhood_payload(walk=92, bike=75, transit=88)
    MockRedfin.return_value = mock_client

    sensor = make_sensor("33333")
    sensor.update()

    assert sensor.data[ATTR_WALK_SCORE] == 92
    assert sensor.data[ATTR_BIKE_SCORE] == 75
    assert sensor.data[ATTR_TRANSIT_SCORE] == 88


@patch("custom_components.redfin.sensor.Redfin")
def test_sensor_scores_none_on_missing_data(MockRedfin):
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
    MockRedfin.return_value = mock_client

    sensor = make_sensor("44444")
    sensor.update()

    assert sensor.data[ATTR_WALK_SCORE] is None
    assert sensor.data[ATTR_BIKE_SCORE] is None
    assert sensor.data[ATTR_TRANSIT_SCORE] is None
