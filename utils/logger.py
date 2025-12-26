import logging
from config import LOG_CONFIG
import os


def init_logger():
    """初始化日志配置"""
    # 创建日志目录
    log_dir = os.path.dirname(LOG_CONFIG['filename'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['level']),
        filename=LOG_CONFIG['filename'],
        format=LOG_CONFIG['format'],
        filemode='a'
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    logging.getLogger().addHandler(console_handler)

    return logging.getLogger(__name__)


logger = init_logger()