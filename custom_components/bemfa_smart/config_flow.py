# bemfa_smart/config_flow.py
"""巴法智能集成的配置流程"""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import selector
import logging

from .const import (
    CONF_USER, DOMAIN, NAME, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
    # 移除 CONF_TEMP_SENSOR_ENTITY_ID 的导入
    CONF_FAN_SPEED_LEVELS, DEFAULT_FAN_SPEED_LEVELS,
    DEVICE_TYPE_FAN # 导入风扇设备类型
)

_LOGGER = logging.getLogger(__name__)

# 将 CONF_TEMP_SENSOR_ENTITY_ID 和 CONF_AC_TOPIC_TO_CONFIGURE 定义在 config_flow.py 内部
CONF_TEMP_SENSOR_ENTITY_ID = "temp_sensor_entity_id" # 重新定义在这里
CONF_AC_TOPIC_TO_CONFIGURE = "ac_topic_to_configure"

# 新增常量用于风扇配置
CONF_FAN_TOPIC_TO_CONFIGURE = "fan_topic_to_configure"
CONF_FAN_SPECIFIC_SPEED_LEVELS = "fan_specific_speed_levels"


class BemfaSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """巴法智能集成的配置流程处理"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """处理用户初始化的配置流程"""
        errors = {}
        if user_input is not None:
            try:
                await self.async_set_unique_id(user_input[CONF_USER][:8])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=NAME,
                    data=user_input,
                    options={
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    }
                )
            except Exception:
                errors["base"] = "invalid_input"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USER): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }),
            errors=errors,
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry):
        """返回选项流处理器"""
        return BemfaSmartOptionsFlowHandler(config_entry)


class BemfaSmartOptionsFlowHandler(config_entries.OptionsFlow):
    """处理集成选项的流程"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """初始化选项流"""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self.coordinator_data = None
        self.current_ac_topic = None
        self.current_ac_name = None
        self.current_fan_topic = None
        self.current_fan_name = None

    async def async_step_init(self, user_input=None):
        """管理选项的初始步骤：选择扫描间隔和要配置的设备类型"""
        _LOGGER.debug("async_step_init called with user_input: %s", user_input)

        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
        await coordinator.async_refresh()
        self.coordinator_data = coordinator.data

        menu_options = {
            "global_settings": "全局设置 (扫描间隔)",
            "configure_ac_sensors": "配置空调温度传感器",
            "configure_fan_levels": "配置风扇挡位数量",
            "finish": "完成并保存配置",
        }

        if user_input is not None:
            choice = user_input.get("menu_choice")
            if choice == "global_settings":
                self.options[CONF_SCAN_INTERVAL] = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                # 直接保存更新，并返回主菜单，而不是停留在同一个菜单
                self.async_create_entry(title="", data=self.options)
                return self.async_show_form(step_id="init", data_schema=self._get_init_schema(menu_options), errors=None)
            elif choice == "configure_ac_sensors":
                return await self.async_step_select_ac_for_sensor()
            elif choice == "configure_fan_levels":
                return await self.async_step_select_fan_for_levels()
            elif choice == "finish":
                return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_init_schema(menu_options)
        )

    def _get_init_schema(self, menu_options):
        """返回初始步骤的Schema"""
        return vol.Schema({
            vol.Required("menu_choice"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": key, "label": value} for key, value in menu_options.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        })


    async def async_step_select_ac_for_sensor(self, user_input=None):
        """选择要配置传感器的空调"""
        _LOGGER.debug("async_step_select_ac_for_sensor called with user_input: %s", user_input)
        air_conditioners = {
            device['topic']: device['name']
            for device in self.coordinator_data
            if device.get('id') == "aircondition"
        }

        ac_options = [
            {"value": "back", "label": "返回主菜单"}
        ]
        ac_options.extend([
            {"value": topic, "label": name} for topic, name in air_conditioners.items()
        ])

        if user_input is not None:
            self.current_ac_topic = user_input.get(CONF_AC_TOPIC_TO_CONFIGURE)
            if self.current_ac_topic == "back":
                return await self.async_step_init()
            elif self.current_ac_topic:
                self.current_ac_name = air_conditioners.get(self.current_ac_topic, "未知空调")
                return await self.async_step_link_sensor()
            else:
                return self.async_show_form(
                    step_id="select_ac_for_sensor",
                    data_schema=vol.Schema({
                        vol.Required(CONF_AC_TOPIC_TO_CONFIGURE): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=ac_options, mode=selector.SelectSelectorMode.DROPDOWN)
                        )
                    }),
                    errors={"base": "invalid_selection"}
                )

        return self.async_show_form(
            step_id="select_ac_for_sensor",
            data_schema=vol.Schema({
                vol.Required(CONF_AC_TOPIC_TO_CONFIGURE): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=ac_options, mode=selector.SelectSelectorMode.DROPDOWN)
                )
            })
        )


    async def async_step_link_sensor(self, user_input=None):
        """链接温度传感器到选定的空调"""
        _LOGGER.debug("async_step_link_sensor called for AC topic: %s with user_input: %s", self.current_ac_topic, user_input)
        errors = {}

        if user_input is not None:
            sensor_entity_id = user_input.get(CONF_TEMP_SENSOR_ENTITY_ID)
            if self.current_ac_topic:
                self.options.setdefault("linked_sensors", {})
                self.options["linked_sensors"][self.current_ac_topic] = sensor_entity_id if sensor_entity_id else None
                _LOGGER.info("Linked sensor %s to AC topic %s", sensor_entity_id, self.current_ac_topic)
                return await self.async_step_select_ac_for_sensor()
            else:
                errors["base"] = "no_ac_selected"

        current_linked_sensor = self.options.get("linked_sensors", {}).get(self.current_ac_topic)

        data_schema = vol.Schema({
            vol.Optional(
                CONF_TEMP_SENSOR_ENTITY_ID,
                default=current_linked_sensor
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature", multiple=False)
            )
        })

        return self.async_show_form(
            step_id="link_sensor",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"ac_name": self.current_ac_name}
        )

    async def async_step_select_fan_for_levels(self, user_input=None):
        """选择要配置挡位数的风扇"""
        _LOGGER.debug("async_step_select_fan_for_levels called with user_input: %s", user_input)
        fans = {
            device['topic']: device['name']
            for device in self.coordinator_data
            if device.get('id') == DEVICE_TYPE_FAN
        }

        fan_options = [
            {"value": "back", "label": "返回主菜单"}
        ]
        fan_options.extend([
            {"value": topic, "label": name} for topic, name in fans.items()
        ])

        if user_input is not None:
            self.current_fan_topic = user_input.get(CONF_FAN_TOPIC_TO_CONFIGURE)
            if self.current_fan_topic == "back":
                return await self.async_step_init()
            elif self.current_fan_topic:
                self.current_fan_name = fans.get(self.current_fan_topic, "未知风扇")
                return await self.async_step_set_fan_levels()
            else:
                return self.async_show_form(
                    step_id="select_fan_for_levels",
                    data_schema=vol.Schema({
                        vol.Required(CONF_FAN_TOPIC_TO_CONFIGURE): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=fan_options, mode=selector.SelectSelectorMode.DROPDOWN)
                        )
                    }),
                    errors={"base": "invalid_selection"}
                )

        return self.async_show_form(
            step_id="select_fan_for_levels",
            data_schema=vol.Schema({
                vol.Required(CONF_FAN_TOPIC_TO_CONFIGURE): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=fan_options, mode=selector.SelectSelectorMode.DROPDOWN)
                )
            })
        )

    async def async_step_set_fan_levels(self, user_input=None):
        """设置选定风扇的挡位数量"""
        _LOGGER.debug("async_step_set_fan_levels called for fan topic: %s with user_input: %s", self.current_fan_topic, user_input)
        errors = {}

        if user_input is not None:
            speed_levels = user_input.get(CONF_FAN_SPECIFIC_SPEED_LEVELS)
            if self.current_fan_topic:
                self.options.setdefault("fan_levels_by_topic", {})
                self.options["fan_levels_by_topic"][self.current_fan_topic] = speed_levels
                _LOGGER.info("Set fan %s levels to %s", self.current_fan_name, speed_levels)
                return await self.async_step_select_fan_for_levels()
            else:
                errors["base"] = "no_fan_selected"

        current_levels = self.options.get("fan_levels_by_topic", {}).get(self.current_fan_topic, DEFAULT_FAN_SPEED_LEVELS)

        data_schema = vol.Schema({
            vol.Required(
                CONF_FAN_SPECIFIC_SPEED_LEVELS,
                default=current_levels
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=5))
        })

        return self.async_show_form(
            step_id="set_fan_levels",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"fan_name": self.current_fan_name}
        )
