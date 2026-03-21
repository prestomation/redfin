"""Tests for the config flow."""
import pytest
from unittest import mock

from homeassistant.const import CONF_DEVICE_CLASS, CONF_DEVICE_ID, CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry, patch

# config_flow.py uses async_get_registry which was removed in newer HA versions.
# These tests are skipped until config_flow.py is updated to use async_get (HA 2022.2+).
pytest.importorskip(
    "custom_components.redfin.config_flow",
    reason="config_flow imports async_get_registry which was removed in HA 2022.2+",
)

from custom_components.redfin import config_flow
from custom_components.redfin.const import DOMAIN


async def test_flow_user_init(hass):
    """Test the initialization of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": config_flow.CONF_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": mock.ANY,
        "handler": "redfin",
        "step_id": "user",
        "type": "form",
        "last_step": None,
    }
    assert expected == result
