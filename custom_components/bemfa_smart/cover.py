"""巴法智能窗帘设备的实现"""

from homeassistant.components.cover import (
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEVICE_TYPE_CURTAIN
from .base_device import BemfaSmartEntity


class BemfaCurtain(BemfaSmartEntity, CoverEntity):
    """巴法智能窗帘设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化窗帘设备"""
        super().__init__(coordinator, config_entry, device_data)
        self._attr_device_class = CoverDeviceClass.CURTAIN
        self._attr_supported_features = (
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.SET_POSITION |
            CoverEntityFeature.STOP
        )
        self._attr_current_cover_position = 0
        self._update_state()

    def _update_state(self): # 保留 _update_state，供 _handle_coordinator_update 调用
        """更新窗帘状态"""
        msg = self.device_data['msg']
        on_state = msg.get('on', False)
        position = msg.get('position', 0)

        if not on_state:
            self._attr_current_cover_position = 0
            self._attr_is_closed = True
        elif position > 0:
            self._attr_current_cover_position = position
            self._attr_is_closed = position == 0
        else:
            # 如果没有位置信息，根据on状态判断
            self._attr_current_cover_position = 100 if on_state else 0
            self._attr_is_closed = not on_state

    @property
    def device_type(self):
        """返回设备类型"""
        return DEVICE_TYPE_CURTAIN

    async def async_open_cover(self, **kwargs):
        """打开窗帘"""
        topic = self.device_data['topic']
        await self.coordinator.async_send_command(topic, "on")

        self.device_data['msg']['on'] = True
        self.device_data['msg']['position'] = 100
        self._attr_current_cover_position = 100
        self._attr_is_closed = False
        self.async_write_ha_state() # 立即更新状态

    async def async_close_cover(self, **kwargs):
        """关闭窗帘"""
        topic = self.device_data['topic']
        await self.coordinator.async_send_command(topic, "off")

        self.device_data['msg']['on'] = False
        self.device_data['msg']['position'] = 0
        self._attr_current_cover_position = 0
        self._attr_is_closed = True
        self.async_write_ha_state() # 立即更新状态

    async def async_set_cover_position(self, position: int, **kwargs):
        """设置窗帘位置"""
        topic = self.device_data['topic']
        msg = f"on#{position}"
        await self.coordinator.async_send_command(topic, msg)

        self.device_data['msg']['on'] = True
        self.device_data['msg']['position'] = position
        self._attr_current_cover_position = position
        self._attr_is_closed = position == 0
        self.async_write_ha_state() # 立即更新状态

    async def async_stop_cover(self, **kwargs):
        """停止窗帘"""
        topic = self.device_data['topic']
        await self.coordinator.async_send_command(topic, "pause")

        # 停止时保持当前位置
        self.async_write_ha_state() # 立即更新状态


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能窗帘平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_CURTAIN:
            entities.append(BemfaCurtain(coordinator, config_entry, device_data))
    
    if entities:
        async_add_entities(entities)