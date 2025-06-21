"""巴法智能灯光设备的实现"""

from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    LightEntityFeature,
    ColorMode
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEVICE_TYPE_LIGHT
from .base_device import BemfaSmartEntity


class BemfaLight(BemfaSmartEntity, LightEntity):
    """巴法智能灯光设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化灯光设备"""
        super().__init__(coordinator, config_entry, device_data)
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF

        self._attr_is_on = device_data['msg'].get('on', False)

    @property
    def device_type(self):
        """返回设备类型"""
        return DEVICE_TYPE_LIGHT

    @property
    def is_on(self):
        """返回灯光是否开启"""
        return self.device_data['msg'].get('on', False)

    async def async_turn_on(self, **kwargs):
        """开启灯光"""
        topic = self.device_data['topic']
        await self.coordinator.async_send_command(topic, "on")
        self.device_data['msg']['on'] = True
        self._attr_color_mode = ColorMode.ONOFF
        self.async_write_ha_state() # 立即更新状态

    async def async_turn_off(self, **kwargs):
        """关闭灯光"""
        topic = self.device_data['topic']
        await self.coordinator.async_send_command(topic, "off")
        self.device_data['msg']['on'] = False
        self._attr_color_mode = ColorMode.ONOFF
        self.async_write_ha_state() # 立即更新状态

    def _update_state(self): # 保留 _update_state，供 _handle_coordinator_update 调用
        """更新灯光实体状态"""
        self._attr_is_on = self.device_data['msg'].get('on', False)
        self._attr_color_mode = ColorMode.ONOFF


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能灯光平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_LIGHT:
            entities.append(BemfaLight(coordinator, config_entry, device_data))
    
    if entities:
        async_add_entities(entities)