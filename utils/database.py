import mysql.connector
from contextlib import contextmanager
from config.config import MYSQL_CONFIG
from utils.logger import setup_logger

logger = setup_logger('database')

@contextmanager
def get_mysql_connection():
    """获取MySQL数据库连接"""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            port=MYSQL_CONFIG['port'],
            charset=MYSQL_CONFIG['charset'],
            consume_results=True  # 自动消费结果
        )
        yield conn
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.close()
                logger.debug("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {str(e)}") 