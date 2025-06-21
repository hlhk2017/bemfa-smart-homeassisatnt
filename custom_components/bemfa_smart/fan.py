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
        self._attr_percentage_step = 20 # 100% / 5挡 = 20% 每挡
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
        """将挡位 (0-5) 转换为百分比 (0-100)"""
        if level == 0:
            return 0
        return min(100, max(0, level * self._attr_percentage_step))

    def _percentage_to_level(self, percentage):
        """将百分比 (0-100) 转换为挡位 (0-5)"""
        if percentage == 0:
            return 0
        if percentage > 80:
            return 5
        elif percentage > 60:
            return 4
        elif percentage > 40:
            return 3
        elif percentage > 20:
            return 2
        else:
            return 1

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
        return 100

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs):
        """开启风扇，如果指定了百分比则设置速度"""
        _LOGGER.debug("BemfaFan async_turn_on called for %s with percentage: %s", self.name, percentage)
        if percentage is None:
            # 如果没有指定百分比，默认开启到最低挡位（20%），或者如果风扇之前有速度且不是0，则恢复该速度
            if self.percentage is None or self.percentage == 0:
                target_percentage = self._attr_percentage_step # 开启到最低速度
            else:
                target_percentage = self.percentage # 保持当前速度如果已设置且不为0
            _LOGGER.debug("未指定百分比，默认开启到/恢复到百分比: %s", target_percentage)
        else:
            target_percentage = percentage
            _LOGGER.debug("指定百分比，开启到百分比: %s", target_percentage)

        await self.async_set_percentage(target_percentage)

    async def async_turn_off(self, **kwargs):
        """关闭风扇"""
        _LOGGER.debug("BemfaFan async_turn_off called for %s", self.name)
        await self.async_set_percentage(0) # 将百分比设置为0以关闭风扇

    async def async_set_percentage(self, percentage: int):
        """设置风扇百分比速度 (包含开关功能)"""
        _LOGGER.debug("BemfaFan async_set_percentage called for %s with percentage: %s", self.name, percentage)
        topic = self.device_data['topic']
        level = self._percentage_to_level(percentage)

        # 根据百分比确定发送 "on" 或 "off"
        if percentage == 0:
            msg = "off"
        else:
            # 开启或设置速度时，保持摇头状态
            shake_state = 1 if self._attr_oscillating else 0
            msg = f"on#{level}#{shake_state}"

        await self.coordinator.async_send_command(topic, msg)

        # 更新实体内部状态
        self.device_data['msg']['on'] = (percentage > 0)
        self.device_data['msg']['level'] = level
        self._attr_percentage = self._level_to_percentage(level)
        self._attr_is_on = (percentage > 0) # 根据百分比更新开关状态
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool):
        """设置风扇摇头"""
        _LOGGER.debug("BemfaFan async_oscillate called for %s with oscillating: %s", self.name, oscillating)
        topic = self.device_data['topic']
        # 确保风扇开启时才发送摇头命令，并使用当前速度
        if not self.is_on:
            # 如果风扇未开启，自动开启到最低挡位并摇头
            _LOGGER.debug("风扇未开启，自动开启到最低挡位并摇头。")
            await self.async_set_percentage(self._attr_percentage_step)
            # async_set_percentage 会更新状态，所以我们只需要用更新后的状态再次发送摇头命令
            current_level = self._percentage_to_level(self._attr_percentage_step)
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