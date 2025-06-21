# bemfa_smart/config_flow.py
"""巴法智能集成的配置流程"""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import selector
import logging

from .const import CONF_USER, DOMAIN, NAME, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

CONF_TEMP_SENSOR_ENTITY_ID = "temp_sensor_entity_id"
CONF_AC_TOPIC_TO_CONFIGURE = "ac_topic_to_configure"

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
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
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
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60))
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
        # self.config_entry = config_entry # <-- 移除这一行！
        self.options = dict(config_entry.options)
        self.coordinator_data = None
        self.current_ac_topic = None
        self.current_ac_name = None

    async def async_step_init(self, user_input=None):
        """管理选项的初始步骤：选择扫描间隔和要配置的空调"""
        _LOGGER.debug("async_step_init called with user_input: %s", user_input)

        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id] # config_entry 是由 OptionsFlow 自动提供的
        await coordinator.async_refresh()
        self.coordinator_data = coordinator.data

        air_conditioners = {
            device['topic']: device['name']
            for device in self.coordinator_data
            if device.get('id') == "aircondition"
        }

        ac_options = []
        if air_conditioners:
            ac_options.append({"value": "none", "label": "不关联传感器 / 完成配置"})
            for topic, name in air_conditioners.items():
                ac_options.append({"value": topic, "label": name})
        else:
            ac_options.append({"value": "no_ac", "label": "未发现空调设备"})

        if user_input is not None:
            self.options[CONF_SCAN_INTERVAL] = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            self.current_ac_topic = user_input.get(CONF_AC_TOPIC_TO_CONFIGURE)

            if self.current_ac_topic == "none" or self.current_ac_topic == "no_ac":
                _LOGGER.debug("User chose not to link sensor or no AC found. Completing flow.")
                return await self._update_options()
            elif self.current_ac_topic:
                self.current_ac_name = air_conditioners.get(self.current_ac_topic, "未知空调")
                _LOGGER.debug("User selected AC: %s (%s). Proceeding to link sensor step.", self.current_ac_name, self.current_ac_topic)
                return await self.async_step_link_sensor()
            else:
                _LOGGER.error("Unexpected state: No AC selected in async_step_init but user_input is not None.")
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_init_schema(air_conditioners),
                    errors={"base": "invalid_selection"}
                )

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_init_schema(air_conditioners)
        )

    def _get_init_schema(self, air_conditioners):
        """返回初始步骤的Schema"""
        ac_options = [
            {"value": "none", "label": "不关联传感器 / 完成配置"}
        ]
        ac_options.extend([
            {"value": topic, "label": name} for topic, name in air_conditioners.items()
        ])

        return vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Optional(
                CONF_AC_TOPIC_TO_CONFIGURE,
                default="none",
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=ac_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="select_ac_for_sensor"
                )
            ),
        })

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
                return await self.async_step_init()
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

    async def _update_options(self):
        """将当前选项保存到配置项中"""
        _LOGGER.debug("Updating config entry options: %s", self.options)
        return self.async_create_entry(title="", data=self.options)
