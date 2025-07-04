# bemfa_smart/climate.py
"""巴法智能空调设备的实现"""

from homeassistant.components.climate import (
    ClimateEntity,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import (
    PRECISION_WHOLE,
    UnitOfTemperature
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging

from .const import (
    DOMAIN,
    DEVICE_TYPE_AIR_CONDITIONER,
    ATTR_ON,
    ATTR_TEMPERATURE
)
# 这里不再从 .const 导入 CONF_TEMP_SENSOR_ENTITY_ID
# from .config_flow import CONF_TEMP_SENSOR_ENTITY_ID # 也不从config_flow导入，直接使用字符串键

from .base_device import BemfaSmartEntity

_LOGGER = logging.getLogger(__name__)


class BemfaAirConditioner(BemfaSmartEntity, ClimateEntity):
    """巴法智能空调设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化空调设备"""
        super().__init__(coordinator, config_entry, device_data)
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            HVACMode.DRY,
        ]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.TURN_OFF |
            ClimateEntityFeature.TURN_ON
        )
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = PRECISION_WHOLE
        self._attr_min_temp = 16
        self._attr_max_temp = 32

        self._attr_fan_modes = ["low", "medium", "high"]

        self._internal_hvac_mode = HVACMode.OFF
        self._internal_target_temperature = 25
        self._internal_fan_mode = "low"

        linked_sensors = config_entry.options.get("linked_sensors", {})
        # 直接使用字符串 "temp_sensor_entity_id" 作为键，因为它不再是导入的常量
        self._current_temp_sensor_entity_id = linked_sensors.get(device_data['topic'])

        if not self._current_temp_sensor_entity_id:
            _LOGGER.warning("未为空调 %s 配置外部温度传感器，将使用目标温度作为当前温度。", self.name)
        else:
            _LOGGER.debug("空调 %s 已关联外部温度传感器: %s", self.name, self._current_temp_sensor_entity_id)

    async def async_added_to_hass(self):
        """当实体添加到Home Assistant时调用。"""
        await super().async_added_to_hass()
        if not hasattr(self.coordinator, 'climate_entities'):
            self.coordinator.climate_entities = []
        self.coordinator.climate_entities.append(self)
        self._update_state()

    @property
    def hvac_mode(self) -> HVACMode | None:
        """返回当前HVAC模式。"""
        return self._attr_hvac_mode

    @property
    def is_on(self) -> bool:
        """返回设备是否开启。"""
        return self._attr_hvac_mode != HVACMode.OFF

    def _update_state(self):
        """更新空调状态。现在会根据API的on/off状态来更新HVAC模式。"""
        msg = self.device_data['msg']
        is_on_from_api = msg.get(ATTR_ON, False)

        api_mode_code = msg.get('mode')
        api_target_temp = msg.get('t')
        api_fan_speed_code = msg.get('level')

        if not is_on_from_api:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_current_temperature = None
            self._attr_target_temperature = self._internal_target_temperature
            self._attr_fan_mode = None
            _LOGGER.debug("_update_state: 检测到API报告设备已关闭，HVAC模式强制设为OFF。")
            return

        if api_mode_code is not None:
            self._internal_hvac_mode = self._mode_to_hvac(api_mode_code)

        if api_target_temp is not None:
            self._internal_target_temperature = int(api_target_temp)

        if api_fan_speed_code is not None:
            self._internal_fan_mode = self._speed_code_to_fan_mode(api_fan_speed_code)

        self._attr_hvac_mode = self._internal_hvac_mode
        self._attr_target_temperature = self._internal_target_temperature
        self._attr_fan_mode = self._internal_fan_mode

        if self._current_temp_sensor_entity_id:
            try:
                if self.hass:
                    sensor_state = self.hass.states.get(self._current_temp_sensor_entity_id)
                    if sensor_state and sensor_state.state not in ('unavailable', 'unknown', None, ''):
                        temp_val = float(sensor_state.state)
                        self._attr_current_temperature = temp_val
                        _LOGGER.debug("_update_state: 从传感器 %s 获取实际温度: %s", self._current_temp_sensor_entity_id, self._attr_current_temperature)
                    else:
                        self._attr_current_temperature = self._attr_target_temperature
                        _LOGGER.warning("_update_state: 无法从传感器 %s 获取有效温度数据（状态: '%s'），使用目标温度作为当前温度。", self._current_temp_sensor_entity_id, sensor_state.state if sensor_state else 'None/Invalid')
                else:
                    self._attr_current_temperature = self._attr_target_temperature
                    _LOGGER.warning("_update_state: self.hass 不可用，无法获取传感器 %s 的数据，使用目标温度作为当前温度。", self._current_temp_sensor_entity_id)
            except (ValueError, TypeError) as e:
                self._attr_current_temperature = self._attr_target_temperature
                _LOGGER.error("_update_state: 传感器 %s 的温度数据格式错误（错误: %s），使用目标温度作为当前温度。", self._current_temp_sensor_entity_id, e)
        else:
            self._attr_current_temperature = self._attr_target_temperature
            _LOGGER.debug("_update_state: 未指定实际温度传感器，使用目标温度作为当前温度。")

        _LOGGER.debug(
            "_update_state: 空调实体内部状态。模式: %s, 目标温度: %s, 实际温度: %s, 风速模式: %s",
            self._attr_hvac_mode, self._attr_target_temperature, self._attr_current_temperature, self._attr_fan_mode
        )

    def _mode_to_hvac(self, mode_code):
        """将巴法模式代码转换为Home Assistant的HVACMode"""
        mode_map = {
            1: HVACMode.AUTO,
            2: HVACMode.COOL,
            3: HVACMode.HEAT,
            4: HVACMode.FAN_ONLY,
            5: HVACMode.DRY,
            6: HVACMode.FAN_ONLY,
            7: HVACMode.AUTO
        }
        return mode_map.get(mode_code, HVACMode.AUTO)

    def _hvac_to_mode(self, hvac_mode):
        """将Home Assistant的HVACMode转换为巴法模式代码"""
        mode_map = {
            HVACMode.AUTO: 1,
            HVACMode.COOL: 2,
            HVACMode.HEAT: 3,
            HVACMode.FAN_ONLY: 4,
            HVACMode.DRY: 5,
            HVACMode.OFF: 0
        }
        return mode_map.get(hvac_mode, 1)

    def _fan_mode_to_speed_code(self, fan_mode):
        """将Home Assistant的风扇模式字符串转换为巴法风速代码 (1-3)"""
        if fan_mode == "low":
            return 1
        elif fan_mode == "medium":
            return 2
        elif fan_mode == "high":
            return 3
        _LOGGER.warning("_fan_mode_to_speed_code: 遇到不支持的风扇模式 '%s'，默认映射到 'low' (1)。", fan_mode)
        return 1

    def _speed_code_to_fan_mode(self, speed_code):
        """将巴法风速代码 (1-3) 转换为Home Assistant的风扇模式字符串"""
        if speed_code == 1:
            return "low"
        elif speed_code == 2:
            return "medium"
        elif speed_code == 3:
            return "high"
        _LOGGER.warning("_speed_code_to_fan_mode: 遇到不支持的速度代码 '%s'，默认映射到 'low'。", speed_code)
        return "low"

    def _generate_command_msg(self):
        """根据内部存储状态生成完整的巴法智能命令消息字符串"""
        if self._internal_hvac_mode == HVACMode.OFF:
            return "off"

        mode_code = self._hvac_to_mode(self._internal_hvac_mode)
        target_temp = self._internal_target_temperature

        if target_temp is None:
            target_temp = self._internal_target_temperature = 25
            _LOGGER.debug("_generate_command_msg: 内部目标温度无效，使用默认值25。")
        elif target_temp < self._attr_min_temp:
            target_temp = self._attr_min_temp
        elif target_temp > self._attr_max_temp:
            target_temp = self._attr_max_temp

        if self._internal_fan_mode is None:
            self._internal_fan_mode = "low"

        fan_speed_code = self._fan_mode_to_speed_code(self._internal_fan_mode)

        msg = f"on#{mode_code}#{int(target_temp)}#{fan_speed_code}"
        return msg

    @property
    def device_type(self):
        """返回设备类型"""
        return DEVICE_TYPE_AIR_CONDITIONER

    async def async_set_temperature(self, **kwargs):
        """设置目标温度"""
        _LOGGER.debug("async_set_temperature: received kwargs: %s", kwargs)
        temperature = kwargs.get('temperature')
        if temperature is None:
            _LOGGER.warning("async_set_temperature: 未提供温度参数。")
            return

        _LOGGER.debug("async_set_temperature: 设置温度为 %s", temperature)

        if temperature < self._attr_min_temp:
            temperature = self._attr_min_temp
            _LOGGER.warning("async_set_temperature: 设置温度低于最小值 %s，已调整为 %s。", self._attr_min_temp, temperature)
        elif temperature > self._attr_max_temp:
            temperature = self._attr_max_temp
            _LOGGER.warning("async_set_temperature: 设置温度高于最大值 %s，已调整为 %s。", self._attr_max_temp, temperature)

        topic = self.device_data['topic']

        self._internal_target_temperature = int(temperature)
        self._attr_target_temperature = self._internal_target_temperature

        msg_command = self._generate_command_msg()
        _LOGGER.debug("async_set_temperature: 发送命令: %s 到主题: %s", msg_command, topic)
        success = await self.coordinator.async_send_command(topic, msg_command)

        if success:
            self.async_write_ha_state()
            _LOGGER.debug("async_set_temperature: 命令发送成功，HA状态已更新。目标温度: %s", self._internal_target_temperature)
        else:
            _LOGGER.error("async_set_temperature: 发送设置温度命令失败！")

    async def async_set_hvac_mode(self, hvac_mode):
        """设置空调的HVAC模式 (包括开关)"""
        _LOGGER.debug("async_set_hvac_mode: 调用模式: %s", hvac_mode)
        topic = self.device_data['topic']

        self._internal_hvac_mode = hvac_mode
        self._attr_hvac_mode = self._internal_hvac_mode

        msg_command = self._generate_command_msg()
        _LOGGER.debug("async_set_hvac_mode: 发送命令: %s 到主题: %s", msg_command, topic)
        success = await self.coordinator.async_send_command(topic, msg_command)

        if success:
            self.async_write_ha_state()
            if hvac_mode == HVACMode.OFF:
                for entity in self.coordinator.get_climate_entities_for_topic(topic):
                    if entity.device_data['msg'].get(ATTR_ON, False):
                        pass
            _LOGGER.debug("async_set_hvac_mode: 命令发送成功，HA状态已更新。")
        else:
            _LOGGER.error("async_set_hvac_mode: 发送设置模式命令失败！")

    async def async_set_fan_mode(self, fan_mode: str):
        """设置风扇模式"""
        _LOGGER.debug("async_set_fan_mode: 调用风扇模式: %s", fan_mode)
        if fan_mode not in self._attr_fan_modes:
            _LOGGER.warning("async_set_fan_mode: 不支持的风扇模式: %s", fan_mode)
            return

        topic = self.device_data['topic']
        self._internal_fan_mode = fan_mode
        self._attr_fan_mode = self._internal_fan_mode

        msg_command = self._generate_command_msg()
        _LOGGER.debug("async_set_fan_mode: 发送命令: %s 到主题: %s", msg_command, topic)
        success = await self.coordinator.async_send_command(topic, msg_command)

        if success:
            self.async_write_ha_state()
            _LOGGER.debug("async_set_fan_mode: 命令发送成功，HA状态已更新。")
        else:
            _LOGGER.error("async_set_fan_mode: 发送设置风扇模式命令失败！")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能空调平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_AIR_CONDITIONER:
            entities.append(BemfaAirConditioner(coordinator, config_entry, device_data))

    if entities:
        async_add_entities(entities)