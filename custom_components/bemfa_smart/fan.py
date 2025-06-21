# bemfa_smart/fan.py
import logging

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEVICE_TYPE_FAN, CONF_FAN_SPEED_LEVELS, DEFAULT_FAN_SPEED_LEVELS # 导入旧常量
from .config_flow import CONF_FAN_SPECIFIC_SPEED_LEVELS # 导入新常量
from .base_device import BemfaSmartEntity

_LOGGER = logging.getLogger(__name__)


class BemfaFan(BemfaSmartEntity, FanEntity):
    """巴法智能风扇设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化风扇设备"""
        super().__init__(coordinator, config_entry, device_data)
        
        # 尝试从配置中获取当前风扇的特定挡位数
        fan_levels_by_topic = config_entry.options.get("fan_levels_by_topic", {})
        self._max_fan_levels = fan_levels_by_topic.get(
            device_data['topic'], # 使用当前风扇的topic作为键
            DEFAULT_FAN_SPEED_LEVELS # 如果未找到，则使用默认值
        )
        
        # 确保 _max_fan_levels 至少为1，避免除零错误
        if self._max_fan_levels < 1:
            self._max_fan_levels = DEFAULT_FAN_SPEED_LEVELS
            _LOGGER.warning("Fan %s configured with invalid speed levels (%s), defaulting to %s.",
                            self.name, fan_levels_by_topic.get(device_data['topic']), self._max_fan_levels)

        # 计算每个挡位的百分比步长
        self._attr_percentage_step = 100 / self._max_fan_levels # 确保 _max_fan_levels > 0 
        
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED |
            FanEntityFeature.OSCILLATE |
            FanEntityFeature.TURN_ON |
            FanEntityFeature.TURN_OFF
        )
        self._attr_oscillating = False
        self._attr_is_on = device_data['msg'].get('on', False)

        self._attr_percentage = 0
        self._update_state()

    def _update_state(self):
        """更新风扇状态"""
        msg = self.device_data['msg']
        new_is_on = msg.get('on', False)

        new_speed_level = msg.get('level')

        if new_is_on:
            if new_speed_level is None or new_speed_level == 0:
                new_speed_level = 1
            new_speed_level = min(new_speed_level, self._max_fan_levels)
            
            self._attr_percentage = self._level_to_percentage(new_speed_level)
            self._attr_oscillating = msg.get('shake', 0) == 1
        else:
            self._attr_percentage = 0
            self._attr_oscillating = False

        self._attr_is_on = new_is_on

    def _level_to_percentage(self, level):
        """将挡位 (0-max_levels) 转换为百分比 (0-100)"""
        if level == 0:
            return 0
        return min(100, max(0, round(level * (100 / self._max_fan_levels))))


    def _percentage_to_level(self, percentage):
        """将百分比 (0-100) 转换为挡位 (0-max_levels)"""
        if percentage == 0:
            return 0
        
        level = round(percentage / (100 / self._max_fan_levels))
        
        return max(1, min(level, self._max_fan_levels))


    @property
    def device_type(self):
        """返回设备类型"""
        return DEVICE_TYPE_FAN

    @property
    def percentage(self) -> int | None:
        """返回当前风扇百分比速度"""
        return self._attr_percentage

    @property
    def speed_count(self) -> int:
        """返回支持的速度档位数量（用于百分比转换）"""
        return self._max_fan_levels

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs):
        """开启风扇，如果指定了百分比则设置速度"""
        _LOGGER.debug("BemfaFan async_turn_on called for %s with percentage: %s", self.name, percentage)
        if percentage is None:
            if self.percentage is None or self.percentage == 0:
                target_percentage = self._level_to_percentage(1)
            else:
                target_percentage = self.percentage
            _LOGGER.debug("未指定百分比，默认开启到/恢复到百分比: %s", target_percentage)
        else:
            target_percentage = percentage
            _LOGGER.debug("指定百分比，开启到百分比: %s", target_percentage)

        await self.async_set_percentage(target_percentage)

    async def async_turn_off(self, **kwargs):
        """关闭风扇"""
        _LOGGER.debug("BemfaFan async_turn_off called for %s", self.name)
        await self.async_set_percentage(0)

    async def async_set_percentage(self, percentage: int):
        """设置风扇百分比速度 (包含开关功能)"""
        _LOGGER.debug("BemfaFan async_set_percentage called for %s with percentage: %s", self.name, percentage)
        topic = self.device_data['topic']
        level = self._percentage_to_level(percentage)

        if percentage == 0:
            msg = "off"
        else:
            shake_state = 1 if self._attr_oscillating else 0
            msg = f"on#{level}#{shake_state}"

        await self.coordinator.async_send_command(topic, msg)

        self.device_data['msg']['on'] = (percentage > 0)
        self.device_data['msg']['level'] = level
        self._attr_percentage = self._level_to_percentage(level)
        self._attr_is_on = (percentage > 0)
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool):
        """设置风扇摇头"""
        _LOGGER.debug("BemfaFan async_oscillate called for %s with oscillating: %s", self.name, oscillating)
        topic = self.device_data['topic']
        
        if not self.is_on:
            _LOGGER.debug("风扇未开启，自动开启到最低挡位并摇头。")
            await self.async_set_percentage(self._level_to_percentage(1))
            current_level = 1
        else:
            current_level = self._percentage_to_level(self.percentage) if self.percentage is not None else 1

        shake = 1 if oscillating else 0
        msg = f"on#{current_level}#{shake}"
        await self.coordinator.async_send_command(topic, msg)

        self.device_data['msg']['shake'] = shake
        self._attr_oscillating = oscillating
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置巴法智能风扇平台"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device_data in coordinator.data:
        if device_data.get('id') == DEVICE_TYPE_FAN:
            entities.append(BemfaFan(coordinator, config_entry, device_data))

    if entities:
        async_add_entities(entities)
