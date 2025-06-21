"""巴法智能集成的配置流程"""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import CONF_USER, DOMAIN, NAME, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL # 导入 CONF_SCAN_INTERVAL 和 DEFAULT_SCAN_INTERVAL


class BemfaSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """巴法智能集成的配置流程处理"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """处理用户初始化的配置流程"""
        errors = {}
        if user_input is not None:
            # 验证user输入
            try:
                # 这里可以添加简单的验证逻辑
                await self.async_set_unique_id(user_input[CONF_USER][:8])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=NAME,
                    data=user_input,
                    options={ # 在这里设置初始选项
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    }
                )
            except Exception as e:
                errors["base"] = "invalid_input"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USER): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)) # 增加扫描间隔选项，范围1-60秒
            }),
            errors=errors,
        )

    async def async_step_options(self, user_input=None):
        """管理集成的选项"""
        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)

        # 获取当前的扫描间隔设置，如果不存在则使用默认值
        scan_interval = self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        options_schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=scan_interval
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60))
        })

        return self.async_show_form(
            step_id="options",
            data_schema=options_schema
        )