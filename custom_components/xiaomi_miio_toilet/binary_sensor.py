import logging
import voluptuous as vol
import asyncio
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
    ATTR_ENTITY_ID
)
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OCCUPANCY,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.exceptions import PlatformNotReady
from miio import Device, DeviceException

DOMAIN = "xiaomi_miio_toilet"
DATA_KEY = 'binary_sensor.xiaomi_miio_toilet'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_STATUS = SERVICE_SCHEMA.extend(
    {vol.Required("status"): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_TO_METHOD = {
    "flush_on": {
        "method": "flush_on",
        "schema": SERVICE_SCHEMA,
    },
    "work_seatheat": {
        "method": "work_seatheat",
        "schema": SERVICE_SCHEMA_STATUS,
    },
    "work_night_led": {
        "method": "work_night_led",
        "schema": SERVICE_SCHEMA_STATUS,
    }
}

def setup_platform(hass, config, async_add_devices, discovery_info=None):
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)

    toilet = XjxToilet(name, host, token)

    hass.data[DATA_KEY][host] = toilet
    async_add_devices([toilet], update_before_add=True)
    
    async def async_service_handler(service):
        method = SERVICE_TO_METHOD.get(service.service)
        params = {key: value for key, value in service.data.items()
                  if key != ATTR_ENTITY_ID}
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [device for device in hass.data[DATA_KEY].values() if
                       device.entity_id in entity_ids]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method['method']):
                continue
            await getattr(device, method['method'])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    for service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[service].get('schema', SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, service, async_service_handler, schema=schema)


class XjxToilet(BinarySensorEntity):
    def __init__(self, name, host, token):
        self._name = name
        self._device = Device(host, token)
        self._state = False
        self._state_attrs = {}
        device_info = self._device.info()
        self._unique_id = "{}-{}".format(device_info.model, device_info.mac_address)

    async def async_update(self):
        try:
            seating = self._device.get_properties(properties=['seating'])
            self._state = seating[0] == 1
        except Exception:
            _LOGGER.error('Update seating state error.', exc_info=True)
        try:
            seatTemp = self._device.get_properties(properties=['seat_temp','status_seatheat'])
            statusLed = self._device.get_properties(properties=['status_led'])
            self._state_attrs.update({
                "status_seatheat": seatTemp[1] == 1,
                "seat_temp": seatTemp[0],
                "status_led": statusLed[0] == 1
            })
        except Exception:
            _LOGGER.error('Update _status_seatheat error.', exc_info=True)

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on based on the state machine."""
        if self._state is None:
            return False
        return self._state

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return DEVICE_CLASS_OCCUPANCY

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    async def flush_on(self,**kwargs):
        try:
            self._device.send('flush_on', [])
        except DeviceException:
            raise PlatformNotReady

    async def work_seatheat(self,**kwargs):
        try:
            self._device.send('work_seatheat', [kwargs["status"]])
            # 开启马桶圈加热必须同时发送马桶圈温度命令
            if kwargs["status"] == 1:
                self._device.send('send_seat_heat', [kwargs["status"]])
        except DeviceException:
            raise PlatformNotReady
    
    async def work_night_led(self,**kwargs):
        try:
            _LOGGER.error('work_night_led'+self._name, exc_info=True)
            self._device.send('work_night_led', [kwargs["status"]])
        except DeviceException:
            raise PlatformNotReady