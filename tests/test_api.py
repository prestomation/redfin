"""Test component api using mocked redfin library."""
import json
from unittest.mock import MagicMock, patch

from custom_components.redfin.const import DOMAIN


def make_avm_response():
    return {
        "errorMessage": "Success",
        "resultCode": 0,
        "payload": {
            "predictedValue": 650000,
            "sectionPreviewText": "Est. $650K",
            "latLong": {"latitude": 36.1, "longitude": -86.8},
            "streetAddress": {"assembledAddress": "1712 Glen Echo Rd Unit C"},
        },
    }


def make_neighborhood_stats_response():
    return {
        "errorMessage": "Success",
        "resultCode": 0,
        "payload": {
            "addressInfo": {"city": "Nashville", "state": "TN"},
            "walkScoreInfo": {
                "walkScoreData": {
                    "walkScore": {"value": 55},
                    "bikeScore": {"value": 40},
                    "transitScore": {"value": 35},
                }
            },
        },
    }


def test_api_call_mocked():
    """Test API call flow using mocked responses."""
    mock_client = MagicMock()
    mock_client.avm_details.return_value = make_avm_response()
    mock_client.neighborhood_stats.return_value = make_neighborhood_stats_response()

    avm = mock_client.avm_details("12345", "")
    assert avm["errorMessage"] == "Success"
    assert avm["resultCode"] == 0
    assert avm["payload"]["predictedValue"] == 650000

    stats = mock_client.neighborhood_stats("12345")
    assert stats["errorMessage"] == "Success"
    assert stats["payload"]["addressInfo"]["city"] == "Nashville"
    assert stats["payload"]["walkScoreInfo"]["walkScoreData"]["walkScore"]["value"] == 55
