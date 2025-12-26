import logging
import os
from config import DM_CONFIG

logger = logging.getLogger(__name__)

# 获取数据库类型（默认达梦数据库）
DB_TYPE = os.environ.get('DB_TYPE', 'dm')


def get_db_connection():
    """获取数据库连接"""
    try:
        if DB_TYPE == 'dm':
            # 达梦数据库连接
            import dmPython
            conn = dmPython.connect(
                user=DM_CONFIG['user'],
                password=DM_CONFIG['password'],
                server=DM_CONFIG['server'],
                port=DM_CONFIG['port']
            )
            logger.info(f"达梦数据库连接成功：{DM_CONFIG['server']}:{DM_CONFIG['port']}")
            return conn
        elif DB_TYPE == 'mysql':
            # MySQL数据库连接
            import pymysql
            conn = pymysql.connect(
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 3306)),
                database=os.environ.get('DB_NAME', 'machine_monitor')
            )
            logger.info(f"MySQL数据库连接成功：{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}")
            return conn
        elif DB_TYPE == 'postgresql':
            # PostgreSQL数据库连接
            import psycopg2
            conn = psycopg2.connect(
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', ''),
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 5432)),
                database=os.environ.get('DB_NAME', 'machine_monitor')
            )
            logger.info(f"PostgreSQL数据库连接成功：{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}")
            return conn
        elif DB_TYPE == 'sqlite':
            # SQLite数据库连接
            import sqlite3
            conn = sqlite3.connect(
                os.environ.get('DB_PATH', 'machine_monitor.db')
            )
            logger.info(f"SQLite数据库连接成功：{os.environ.get('DB_PATH')}")
            return conn
        else:
            raise ValueError(f"不支持的数据库类型：{DB_TYPE}")
    except Exception as e:
        logger.error(f"数据库连接失败：{str(e)}")
        raise


def init_db():
    """初始化数据库（仅验证连接，表已通过 SQL 脚本创建）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 根据数据库类型执行不同的测试查询
        if DB_TYPE == 'dm':
            cursor.execute("SELECT 1 FROM DUAL")  # 达梦测试查询
        elif DB_TYPE in ['mysql', 'postgresql']:
            cursor.execute("SELECT 1")  # MySQL/PostgreSQL测试查询
        elif DB_TYPE == 'sqlite':
            cursor.execute("SELECT 1")  # SQLite测试查询
        
        cursor.fetchone()
        conn.close()
        logger.info(f"{DB_TYPE}数据库连接成功，初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败：{str(e)}")
        raise

# 全局导出
__all__ = ['get_db_connection', 'init_db']