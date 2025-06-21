# bemfa_smart/const.py
"""巴法智能集成的常量定义"""

DOMAIN = "bemfa_smart"
NAME = "巴法智能"

CONF_USER = "user"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FAN_SPEED_LEVELS = "fan_speed_levels" 

DEFAULT_SCAN_INTERVAL = 30  # 30秒扫描一次
DEFAULT_FAN_SPEED_LEVELS = 3 # 默认风扇挡位为3 (低、中、高)

# 设备类型
DEVICE_TYPE_LIGHT = "light"
DEVICE_TYPE_AIR_CONDITIONER = "aircondition"
DEVICE_TYPE_FAN = "fan"
DEVICE_TYPE_CURTAIN = "curtain"
DEVICE_TYPE_SENSOR = "sensor"
DEVICE_TYPE_OUTLET = "outlet"
DEVICE_TYPE_SWITCH = "switch"

# 设备状态字段
ATTR_ON = "on"
ATTR_TEMPERATURE = "t"
ATTR_HUMIDITY = "h"
ATTR_UNIT = "unit"
ATTR_LAST_UPDATED = "unix"

# API相关
API_BASE_URL = "https://pro.bemfa.com/v4/app/v1"
API_HOME_ROOM = f"{API_BASE_URL}/homeRoom"
API_POST_MSG = "https://pro.bemfa.com/vv/postmsg2"