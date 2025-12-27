import logging
import os
import psycopg2
from config import PG_CONFIG

logger = logging.getLogger(__name__)

# 数据库类型固定为postgresql
DB_TYPE = 'postgresql'

def get_db_connection():
    """获取PostgreSQL数据库连接"""
    try:
        # PostgreSQL数据库连接
        conn = psycopg2.connect(
            user=PG_CONFIG['user'],
            password=PG_CONFIG['password'],
            host=PG_CONFIG['server'],
            port=PG_CONFIG['port'],
            database=PG_CONFIG['database']
        )
        logger.info(f"PostgreSQL数据库连接成功：{PG_CONFIG['server']}:{PG_CONFIG['port']}")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL数据库连接失败：{str(e)}")
        raise

def init_db():
    """初始化数据库（仅验证连接，表已通过 SQL 脚本创建）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 执行PostgreSQL测试查询
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        logger.info(f"PostgreSQL数据库连接成功，初始化完成")
    except Exception as e:
        logger.error(f"PostgreSQL数据库初始化失败：{str(e)}")
        raise

# 全局导出
__all__ = ['get_db_connection', 'init_db']
