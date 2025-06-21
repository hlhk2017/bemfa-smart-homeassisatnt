"""巴法智能设备的基础类"""

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class BemfaSmartEntity(CoordinatorEntity, Entity):
    """巴法智能设备的基础实体类"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化基础实体"""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.device_data = device_data
        self._attr_unique_id = f"bemfa_{device_data['topic']}"
        self._attr_name = device_data['name']
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_data['topic'])},
            "name": device_data['name'],
            "manufacturer": "巴法智能",
            "model": f"Bemfa Device ({device_data['id']})",
        }

    @property
    def available(self):
        """设备是否可用"""
        # 可以根据最后更新时间判断设备是否离线
        last_updated = self.device_data.get("unix", 0)
        # 如果设备超过10分钟未更新，视为不可用
        # 并且协调器本身也必须成功更新过
        return (self.coordinator.last_update_success and 
                (self.hass.loop.time() - last_updated) < 600)

    def update_device_state(self):
        """更新设备状态数据"""
        # 确保 coordinator.data 非空，以防协调器尚未获取到数据或获取失败
        if self.coordinator.data is None:
            return

        # 从协调器最新的数据中找到当前设备的最新状态
        self.device_data = next(
            (device for device in self.coordinator.data if device['topic'] == self.device_data['topic']),
            self.device_data
        )

    def _handle_coordinator_update(self) -> None:
        """处理协调器更新的数据。"""
        # 这个方法会在协调器数据更新时自动调用
        self.update_device_state() # 更新实体内部的设备数据
        self._update_state()       # 调用实体特有的状态更新逻辑
        self.async_write_ha_state() # 通知Home Assistant更新实体状态