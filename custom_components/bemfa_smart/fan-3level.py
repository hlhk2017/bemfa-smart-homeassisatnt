import logging

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEVICE_TYPE_FAN
from .base_device import BemfaSmartEntity

_LOGGER = logging.getLogger(__name__) # 初始化日志记录器


class BemfaFan(BemfaSmartEntity, FanEntity):
    """巴法智能风扇设备"""

    def __init__(self, coordinator, config_entry, device_data):
        """初始化风扇设备"""
        super().__init__(coordinator, config_entry, device_data)
        self._attr_percentage_step = 33 # Changed for 3 speeds (100 / 3) roughly
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

        if new_is_on: # 如果风扇根据API是开启的
            if new_speed_level is None: # 并且API没有报告具体的挡位
                if self._attr_percentage > 0: # 如果当前实体有记录的百分比
                    new_speed_level = self._percentage_to_level(self._attr_percentage)
                    if new_speed_level == 0:
                        new_speed_level = 1
                else:
                    new_speed_level = 1

            if new_speed_level == 0 and new_is_on:
                new_speed_level = 1

            self._attr_percentage = self._level_to_percentage(new_speed_level)
            self._attr_oscillating = msg.get('shake', 0) == 1
        else: # 如果风扇根据API是关闭的
            self._attr_percentage = 0
            self._attr_oscillating = False

        self._attr_is_on = new_is_on

    def _level_to_percentage(self, level):
        """将挡位 (0-3) 转换为百分比 (0-100)"""
        if level == 0:
            return 0
        elif level == 1: # Low
            return 33
        elif level == 2: # Medium
            return 66
        elif level == 3: # High
            return 100
        # Fallback for unexpected levels
        _LOGGER.warning("Encountered unsupported fan level '%s', mapping to 0 percentage.", level)
        return 0

    def _percentage_to_level(self, percentage):
        """将百分比 (0-100) 转换为挡位 (0-3)"""
        if percentage == 0:
            return 0
        elif percentage <= 33: # Low
            return 1
        elif percentage <= 66: # Medium
            return 2
        else: # High (covers > 66 to 100)
            return 3

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
        return 3 # Only 3 speeds (low, medium, high)

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs):
        """开启风扇，如果指定了百分比则设置速度"""
        _LOGGER.debug("BemfaFan async_turn_on called for %s with percentage: %s", self.name, percentage)
        if percentage is None:
            # 如果没有指定百分比，默认开启到最低挡位（33%），或者如果风扇之前有速度且不是0，则恢复该速度
            if self.percentage is None or self.percentage == 0:
                target_percentage = 33 # Open to lowest speed
            else:
                target_percentage = self.percentage # Keep current speed if set and not 0
            _LOGGER.debug("No percentage specified, defaulting to/restoring to percentage: %s", target_percentage)
        else:
            target_percentage = percentage
            _LOGGER.debug("Percentage specified, turning on to percentage: %s", target_percentage)

        await self.async_set_percentage(target_percentage)

    async def async_turn_off(self, **kwargs):
        """关闭风扇"""
        _LOGGER.debug("BemfaFan async_turn_off called for %s", self.name)
        await self.async_set_percentage(0) # Set percentage to 0 to turn off the fan

    async def async_set_percentage(self, percentage: int):
        """设置风扇百分比速度 (包含开关功能)"""
        _LOGGER.debug("BemfaFan async_set_percentage called for %s with percentage: %s", self.name, percentage)
        topic = self.device_data['topic']
        level = self._percentage_to_level(percentage)

        # Determine to send "on" or "off" based on percentage
        if percentage == 0:
            msg = "off"
        else:
            # When turning on or setting speed, keep oscillation state
            shake_state = 1 if self._attr_oscillating else 0
            msg = f"on#{level}#{shake_state}"

        await self.coordinator.async_send_command(topic, msg)

        # Update entity internal state
        self.device_data['msg']['on'] = (percentage > 0)
        self.device_data['msg']['level'] = level
        self._attr_percentage = self._level_to_percentage(level)
        self._attr_is_on = (percentage > 0) # Update on/off state based on percentage
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool):
        """设置风扇摇头"""
        _LOGGER.debug("BemfaFan async_oscillate called for %s with oscillating: %s", self.name, oscillating)
        topic = self.device_data['topic']
        # Ensure that the fan is on when sending the oscillation command, and use the current speed.
        if not self.is_on:
            # If the fan is not on, automatically turn it on to the lowest setting and oscillate
            _LOGGER.debug("Fan is off, automatically turning on to lowest setting and oscillating.")
            await self.async_set_percentage(33) # Changed for 3 speeds
            # async_set_percentage will update the state, so we just need to send the oscillation command again with the updated state
            current_level = self._percentage_to_level(33) # Changed for 3 speeds
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