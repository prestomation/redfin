"""Support for estimate data from redfin.com."""
from datetime import timedelta
import logging

import voluptuous as vol
from redfin import Redfin
from homeassistant import config_entries, core

from .const import (DEFAULT_NAME, DOMAIN, CONF_PROPERTIES, ATTRIBUTION, DEFAULT_SCAN_INTERVAL, CONF_PROPERTY_IDS,
                    ICON, CONF_PROPERTY_ID, ATTR_AMOUNT, ATTR_AMOUNT_FORMATTED, ATTR_ADDRESS, ATTR_FULL_ADDRESS,
                    ATTR_CURRENCY, ATTR_STREET_VIEW, ATTR_REDFIN_URL, RESOURCE_URL, ATTR_UNIT_OF_MEASUREMENT,
                    ATTR_WALK_SCORE, ATTR_BIKE_SCORE, ATTR_TRANSIT_SCORE)
from homeassistant.core import callback
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorStateClass
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_SCAN_INTERVAL
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PROPERTY_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                     ): vol.All(vol.Coerce(int)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

SCAN_INTERVAL = timedelta(hours=12)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [RedfinDataSensor(config[CONF_NAME], params, config[CONF_SCAN_INTERVAL])
               for params in config[CONF_PROPERTIES]]
    async_add_entities(sensors, update_before_add=True)


class RedfinDataSensor(SensorEntity):
    """Implementation of a Redfin sensor."""

    def __init__(self, name, params, interval):
        """Initialize the sensor."""
        self._name = name
        self.params = params
        self.data = None
        self.address = f"property {params[CONF_PROPERTY_ID]}"
        self.property_id = params[CONF_PROPERTY_ID]
        self._state = None
        self._interval = timedelta(minutes=interval)
        self._unsub_timer = None

    @property
    def should_poll(self):
        """Disable built-in HA polling — we use a custom timer."""
        return False

    @property
    def unique_id(self):
        """Return the property_id."""
        return self.params[CONF_PROPERTY_ID]

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} {self.address}"

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            # return self._state
            return round(float(self._state), 1)
        except ValueError:
            return None

    @property
    def state_class(self):
        # set state_class to 'measurement' so long-term statistics are generated
        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        if self.data is not None:
            attributes = self.data
        return attributes

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    async def async_added_to_hass(self):
        """Start custom polling."""

        @callback
        def async_update(event_time=None):
            """Update the entity."""
            self.async_schedule_update_ha_state(True)

        self._unsub_timer = async_track_time_interval(self.hass, async_update, self._interval)

    async def async_will_remove_from_hass(self):
        """Clean up timer on entity removal."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    def update(self):
        """Get the latest data and update the states."""

        client = Redfin()
        property_id = self.params[CONF_PROPERTY_ID]

        try:
            avm_details = client.avm_details(property_id, "")
            if avm_details["resultCode"] != 0:
                _LOGGER.error("The API returned: %s",
                              avm_details["errorMessage"])
                return
        except Exception as err:
            _LOGGER.error("Unable to retrieve avm_details from Redfin API: %s", err)
            return
        _LOGGER.debug("%s - The avm_details API returned: %s for property id: %s",
                      self._name, avm_details["errorMessage"], property_id)

        try:
            neighborhood_stats = client.neighborhood_stats(property_id)
            if neighborhood_stats["resultCode"] != 0:
                _LOGGER.error("The neighborhood_stats API returned: %s",
                              neighborhood_stats["errorMessage"])
                return
        except Exception as err:
            _LOGGER.error("Unable to retrieve neighborhood_stats from Redfin API: %s", err)
            return
        _LOGGER.debug("%s - The neighborhood_stats API returned: %s for property id: %s",
                      self._name, neighborhood_stats["errorMessage"], property_id)

        # Extract address
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

        # Extract lat/long and build street view URL
        try:
            lat = avm_details["payload"]["latLong"]["latitude"]
            lng = avm_details["payload"]["latLong"]["longitude"]
            streetViewUrl = f"https://www.google.com/maps/@{lat},{lng},3a,75y,90t/data=!3m6!1e1"
        except (KeyError, TypeError):
            streetViewUrl = "Not Set"

        # Redfin URL (generic — no slug available from API)
        redfinUrl = f"https://www.redfin.com/home/{property_id}"

        # AVM estimated value
        if 'predictedValue' in avm_details["payload"]:
            predictedValue = avm_details["payload"]["predictedValue"]
        else:
            predictedValue = 'Not Set'

        if 'sectionPreviewText' in avm_details["payload"]:
            sectionPreviewText = avm_details["payload"]["sectionPreviewText"]
        else:
            sectionPreviewText = 'Not Set'

        # Walk/bike/transit scores
        try:
            score_data = neighborhood_stats["payload"]["walkScoreInfo"]["walkScoreData"]
            walk_score = score_data["walkScore"]["value"]
            bike_score = score_data["bikeScore"]["value"]
            transit_score = score_data["transitScore"]["value"]
        except (KeyError, TypeError):
            walk_score = bike_score = transit_score = None

        details = {}
        details[ATTR_AMOUNT] = predictedValue
        details[ATTR_CURRENCY] = "USD"
        details[ATTR_UNIT_OF_MEASUREMENT] = details[ATTR_CURRENCY]
        details[ATTR_AMOUNT_FORMATTED] = sectionPreviewText
        details[ATTR_ADDRESS] = address_line
        details[ATTR_FULL_ADDRESS] = self.address
        details[ATTR_REDFIN_URL] = redfinUrl
        details[ATTR_STREET_VIEW] = streetViewUrl
        details[ATTR_WALK_SCORE] = walk_score
        details[ATTR_BIKE_SCORE] = bike_score
        details[ATTR_TRANSIT_SCORE] = transit_score
        details[CONF_PROPERTY_ID] = property_id
        details[ATTR_ATTRIBUTION] = ATTRIBUTION

        self.data = details

        if self.data is not None:
            self._state = self.data[ATTR_AMOUNT]
        else:
            self._state = None
            _LOGGER.error("Unable to get Redfin estimate from response")
