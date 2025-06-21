# bemfa_smart/__init__.py
"""巴法智能集成的初始化"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

from .const import DOMAIN, CONF_USER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import BemfaSmartCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """设置巴法智能集成"""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """从配置项设置巴法智能集成"""
    user = entry.data[CONF_USER]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = BemfaSmartCoordinator(
        hass,
        user,
        scan_interval
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["light", "climate", "fan", "cover", "sensor", "switch"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """卸载配置项"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["light", "climate", "fan", "cover", "sensor", "switch"])
    if unload_ok:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
