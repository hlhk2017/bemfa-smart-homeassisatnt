"""巴法智能传感器设备的实现"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DEVICE_TYPE_SENSOR,
    ATTR_TEMPERATURE,
    ATTR_HUMIDITY,
    ATTR_UNIT
)
from .base_device import BemfaSmartEntity


class BemfaSensor(BemfaSmartEntity, SensorEntity):
    """巴法智能传感器设备"""

    def __init__(self, coordinator, config_entry, device_data, sensor_type):
        """初始化传感器设备"""
        super().__init__(coordinator, config_entry, device_data)
        self.sensor_type = sensor_type
        self._attr_unique_id = f"bemfa_{device_data['topic']}_{sensor_type}"
        self._attr_native_unit_of_measurement = self._get_unit()
        self._update_state()

    def _get_unit(self):
        """获取传感器单位"""
        units = self.device_data.get(ATTR_UNIT, [])
        if self.sensor_type == ATTR_TEMPERATURE and units and len(units) > 0:
            return units[0]
        if self.sensor_type == ATTR_HUMIDITY and units and len(units) > 1:
            return units[1]
        return None

    def _update_state(self): # 保留 _update_state，供 _handle_coordinator_update 调用
        """更新传感器状态"""
        msg = self.device_data['msg']
        self._attr_native_value = msg.get(self.sensor_type)

    @property
    def device_type(self):
        """返回设备类型"""
        return DEVICE_TYPE_SENSOR

    @property
    def name(self):
        """返回传感器名称"""
        name_map = {
            ATTR_TEMPERATURE: f"{super().name} 温度",
            ATTR_HUMIDITY: f"{super().name} 湿度"
        }
        return name_map.get(self.sensor_type, super().name)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能传感器平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_SENSOR:
            msg = device_data.get('msg', {})
            if ATTR_TEMPERATURE in msg:
                entities.append(BemfaSensor(coordinator, config_entry, device_data, ATTR_TEMPERATURE))
            if ATTR_HUMIDITY in msg:
                entities.append(BemfaSensor(coordinator, config_entry, device_data, ATTR_HUMIDITY))
    
    if entities:
        async_add_entities(entities)