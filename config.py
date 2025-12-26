import os

# 数据库配置（达梦DM8）- 支持从环境变量读取
DM_CONFIG = {
    'user': os.environ.get('DM_USER', 'SYSDBA'),
    'password': os.environ.get('DM_PASSWORD', 'SYSDBA'),
    'server': os.environ.get('DM_SERVER', 'localhost'),
    'port': int(os.environ.get('DM_PORT', 5236)),
    'database': os.environ.get('DM_DATABASE', 'DAMENG'),
    'schema': os.environ.get('DM_SCHEMA', 'DEV')
}

# Flask配置
SECRET_KEY = 'machine_monitor_2024_123'
DEBUG = True
PERMANENT_SESSION_LIFETIME = 3600  # Session有效期1小时

# 监控配置
HEARTBEAT_TIMEOUT = 30  # 设备离线判定时间（秒）
WEBSOCKET_INTERVAL = 3  # 实时数据推送间隔（秒）

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'filename': 'logs/machine_monitor.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}