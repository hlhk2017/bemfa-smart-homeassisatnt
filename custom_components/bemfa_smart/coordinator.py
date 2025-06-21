"""巴法智能集成的数据协调器"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import asyncio
import aiohttp
import logging
from datetime import timedelta

from .const import (
    DOMAIN, API_BASE_URL, API_HOME_ROOM, API_POST_MSG,
    CONF_USER, DEFAULT_SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)


class BemfaSmartCoordinator(DataUpdateCoordinator):
    """负责从巴法智能API获取数据的协调器"""

    def __init__(
        self,
        hass: HomeAssistant,
        user: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL
    ):
        """初始化协调器"""
        self.user = user
        self.session = aiohttp.ClientSession()
        update_interval = timedelta(seconds=scan_interval)
        _LOGGER.debug("BemfaSmartCoordinator initializing with scan_interval: %d seconds", scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.climate_entities = [] # 确保这一行存在并正确初始化


    def get_climate_entities_for_topic(self, topic: str):
        """根据topic获取相关的气候实体"""
        return [entity for entity in self.climate_entities if entity.device_data['topic'] == topic]


    async def _async_update_data(self):
        """从API获取最新数据"""
        _LOGGER.debug("BemfaSmartCoordinator fetching new data from API.")
        try:
            url = f"{API_HOME_ROOM}?user={self.user}"
            async with self.session.get(url) as response:
                _LOGGER.debug("API request URL: %s, Status: %d", url, response.status)
                if response.status != 200:
                    response.raise_for_status()
                data = await response.json()
                if data.get("code") != 0:
                    _LOGGER.error("API返回错误: %s", data.get('msg'))
                    raise UpdateFailed(f"API返回错误: {data.get('msg')}")
                _LOGGER.debug("API数据获取成功，共 %d 个设备", len(data.get("data", [])))
                return data.get("data", [])
        except aiohttp.ClientError as e:
            _LOGGER.error("API请求失败: %s", str(e))
            raise UpdateFailed(f"API请求失败: {str(e)}") from e
        except Exception as e:
            _LOGGER.error("获取数据失败: %s", str(e))
            raise UpdateFailed(f"获取数据失败: {str(e)}") from e

    async def async_send_command(self, topic: str, msg: str, device_type: int = 3):
        """向设备发送控制命令"""
        try:
            url = f"{API_POST_MSG}"
            payload = f"user={self.user}&topic={topic}&msg={msg}&type={device_type}"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                "User-Agent": "Dart/3.7 (dart:io)"
            }
            _LOGGER.debug("Sending command to topic: %s with msg: %s", topic, msg)
            async with self.session.post(url, data=payload, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error("发送命令失败，状态码: %d", response.status)
                    return False
                result = await response.text()
                _LOGGER.debug("命令发送结果: %s", result)
                return True
        except Exception as e:
            _LOGGER.error("发送命令异常: %s", str(e))
            return False

    async def async_close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None