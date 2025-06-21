# bemfa_smart/switch.py
"""巴法智能开关设备的实现 (通用开关和空调开关)"""

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass # 导入 SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging

from .const import DOMAIN, DEVICE_TYPE_AIR_CONDITIONER, DEVICE_TYPE_OUTLET, DEVICE_TYPE_SWITCH, ATTR_ON # 导入 DEVICE_TYPE_SWITCH
from .base_device import BemfaSmartEntity

_LOGGER = logging.getLogger(__name__)

# --- 通用开关实体 ---
class BemfaSmartSwitch(BemfaSmartEntity, SwitchEntity):
    """巴法智能通用开关设备 (类型: outlet 或 switch)"""

    def __init__(self, coordinator, config_entry, device_data):
        super().__init__(coordinator, config_entry, device_data)
        self._attr_unique_id = f"bemfa_{device_data['topic']}_universal_switch" # 统一unique_id
        self._attr_name = device_data['name']

        # 根据设备ID设置设备类别，以获取正确图标
        if device_data.get('id') == DEVICE_TYPE_OUTLET:
            self._attr_device_class = SwitchDeviceClass.OUTLET
        elif device_data.get('id') == DEVICE_TYPE_SWITCH:
            self._attr_device_class = SwitchDeviceClass.SWITCH # 默认为通用开关图标
        else:
            self._attr_device_class = None # 未知类型不设置

        self._update_state()

    def _update_state(self):
        msg = self.device_data['msg']
        self._attr_is_on = msg.get(ATTR_ON, False)
        _LOGGER.debug("BemfaSmartSwitch _update_state: %s is_on: %s", self.name, self.is_on)

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("BemfaSmartSwitch async_turn_on called for %s", self.name)
        topic = self.device_data['topic']
        success = await self.coordinator.async_send_command(topic, "on")
        if success:
            self.device_data['msg'][ATTR_ON] = True
            self.async_write_ha_state()
            _LOGGER.debug("BemfaSmartSwitch: %s 开启命令发送成功。", self.name)
        else:
            _LOGGER.error("BemfaSmartSwitch: %s 开启命令发送失败。", self.name)

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("BemfaSmartSwitch async_turn_off called for %s", self.name)
        topic = self.device_data['topic']
        success = await self.coordinator.async_send_command(topic, "off")
        if success:
            self.device_data['msg'][ATTR_ON] = False
            self.async_write_ha_state()
            _LOGGER.debug("BemfaSmartSwitch: %s 关闭命令发送成功。", self.name)
        else:
            _LOGGER.error("BemfaSmartSwitch: %s 关闭命令发送失败。", self.name)

    @property
    def device_type(self):
        # 这个属性通常不再直接用于类型判断，而是直接通过 device_data['id']
        return self.device_data.get('id')


# --- 空调开关实体 ---
class BemfaAirConditionerSwitch(BemfaSmartEntity, SwitchEntity):
    """巴法智能空调开关设备 (类型: aircondition)"""

    def __init__(self, coordinator, config_entry, device_data):
        super().__init__(coordinator, config_entry, device_data)
        self._attr_unique_id = f"bemfa_{device_data['topic']}_ac_switch"
        self._attr_name = f"{device_data['name']} 空调开关"
        self._attr_device_class = SwitchDeviceClass.SWITCH # 空调开关也使用通用开关图标
        self._update_state()

    def _update_state(self):
        msg = self.device_data['msg']
        self._attr_is_on = msg.get(ATTR_ON, False)
        _LOGGER.debug("BemfaAirConditionerSwitch _update_state: %s is_on: %s", self.name, self.is_on)

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("BemfaAirConditionerSwitch async_turn_on called for %s", self.name)
        topic = self.device_data['topic']
        success = await self.coordinator.async_send_command(topic, "on#1#25#1")
        if success:
            self.device_data['msg'][ATTR_ON] = True
            self.async_write_ha_state()
            _LOGGER.debug("BemfaAirConditionerSwitch: %s 开启命令发送成功。", self.name)
            for entity in self.coordinator.get_climate_entities_for_topic(topic):
                entity.async_schedule_update_ha_state(True)
        else:
            _LOGGER.error("BemfaAirConditionerSwitch: %s 开启命令发送失败。", self.name)

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("BemfaAirConditionerSwitch async_turn_off called for %s", self.name)
        topic = self.device_data['topic']
        success = await self.coordinator.async_send_command(topic, "off")
        if success:
            self.device_data['msg'][ATTR_ON] = False
            self.async_write_ha_state()
            _LOGGER.debug("BemfaAirConditionerSwitch: %s 关闭命令发送成功。", self.name)
            for entity in self.coordinator.get_climate_entities_for_topic(topic):
                entity.async_schedule_update_ha_state(True)
        else:
            _LOGGER.error("BemfaAirConditionerSwitch: %s 关闭命令发送失败。", self.name)

    @property
    def device_type(self):
        return DEVICE_TYPE_AIR_CONDITIONER


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能开关平台 (通用开关和空调开关)"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device_data in coordinator.data:
        device_id = device_data.get('id')
        if device_id == DEVICE_TYPE_OUTLET: # 插座
            entities.append(BemfaSmartSwitch(coordinator, config_entry, device_data))
        elif device_id == DEVICE_TYPE_SWITCH: # 普通开关
             entities.append(BemfaSmartSwitch(coordinator, config_entry, device_data)) # 同样使用 BemfaSmartSwitch
        elif device_id == DEVICE_TYPE_AIR_CONDITIONER: # 空调开关
            if ATTR_ON in device_data.get('msg', {}):
                entities.append(BemfaAirConditionerSwitch(coordinator, config_entry, device_data))

    if entities:
        async_add_entities(entities)