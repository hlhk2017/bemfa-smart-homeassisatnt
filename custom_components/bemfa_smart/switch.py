"""巴法智能空调开关设备的实现"""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging

from .const import DOMAIN, DEVICE_TYPE_AIR_CONDITIONER, ATTR_ON
from .base_device import BemfaSmartEntity

_LOGGER = logging.getLogger(__name__)


class BemfaAirConditionerSwitch(BemfaSmartEntity, SwitchEntity):
    """巴法智能空调开关设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化空调开关实体"""
        super().__init__(coordinator, config_entry, device_data)
        self._attr_unique_id = f"bemfa_{device_data['topic']}_switch"
        self._attr_name = f"{device_data['name']} 开关"
        self._update_state()

    def _update_state(self):
        """更新开关状态"""
        msg = self.device_data['msg']
        self._attr_is_on = msg.get(ATTR_ON, False)
        _LOGGER.debug("BemfaAirConditionerSwitch _update_state: %s is_on: %s", self.name, self.is_on)


    async def async_turn_on(self, **kwargs):
        """开启空调"""
        _LOGGER.debug("BemfaAirConditionerSwitch async_turn_on called for %s", self.name)
        topic = self.device_data['topic']
        # 发送一个开启命令，这里使用一个默认的初始模式、温度和风速
        # 假设：自动模式 (1)，25度，低风 (1)
        success = await self.coordinator.async_send_command(topic, "on#1#25#1")
        if success:
            self.device_data['msg'][ATTR_ON] = True
            self.async_write_ha_state()
            _LOGGER.debug("BemfaAirConditionerSwitch: %s 开启命令发送成功。", self.name)
            # 立即触发气候实体的更新，使其状态（特别是HVAC模式）能够快速响应
            for entity in self.coordinator.get_climate_entities_for_topic(topic):
                entity.async_schedule_update_ha_state(True)
        else:
            _LOGGER.error("BemfaAirConditionerSwitch: %s 开启命令发送失败。", self.name)


    async def async_turn_off(self, **kwargs):
        """关闭空调"""
        _LOGGER.debug("BemfaAirConditionerSwitch async_turn_off called for %s", self.name)
        topic = self.device_data['topic']
        success = await self.coordinator.async_send_command(topic, "off")
        if success:
            self.device_data['msg'][ATTR_ON] = False
            self.async_write_ha_state()
            _LOGGER.debug("BemfaAirConditionerSwitch: %s 关闭命令发送成功。", self.name)
            # 立即触发气候实体的更新，使其状态（特别是HVAC模式）能够快速响应
            for entity in self.coordinator.get_climate_entities_for_topic(topic):
                entity.async_schedule_update_ha_state(True)
        else:
            _LOGGER.error("BemfaAirConditionerSwitch: %s 关闭命令发送失败。", self.name)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能空调开关平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_AIR_CONDITIONER:
            entities.append(BemfaAirConditionerSwitch(coordinator, config_entry, device_data))

    if entities:
        async_add_entities(entities)