import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """检查数据库结构和内容"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info("数据库表结构：")
        for table in tables:
            table_name = table[0]
            logger.info(f"\n表名：{table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            logger.info("列信息：")
            for col in columns:
                logger.info(f"  {col[1]} ({col[2]})")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            logger.info(f"记录数：{count}")
            
            # 获取一行示例数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                logger.info("示例数据：")
                logger.info(f"  {sample}")
            
            logger.info("-" * 50)
            
    except Exception as e:
        logger.error(f"检查数据库失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def check_sectors():
    """检查板块数据"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 检查板块表
        cursor.execute("SELECT COUNT(*) FROM sectors")
        sector_count = cursor.fetchone()[0]
        logger.info(f"板块表中共有 {sector_count} 条记录")
        
        # 检查板块成分股关系表
        cursor.execute("SELECT COUNT(*) FROM sector_stocks")
        stock_count = cursor.fetchone()[0]
        logger.info(f"板块成分股关系表中共有 {stock_count} 条记录")
        
        # 获取板块详细信息
        cursor.execute('''
            SELECT 
                s.sector_id, 
                s.sector_name, 
                s.sector_type,
                COUNT(ss.stock_code) as stock_count
            FROM sectors s
            LEFT JOIN sector_stocks ss ON s.sector_id = ss.sector_id
            GROUP BY s.sector_id, s.sector_name, s.sector_type
        ''')
        
        sectors = cursor.fetchall()
        logger.info("\n板块详细信息：")
        for sector in sectors:
            logger.info(f"ID: {sector[0]}, 名称: {sector[1]}, 类型: {sector[2]}, 股票数: {sector[3]}")
            
        # 检查成分股详细信息
        cursor.execute('''
            SELECT 
                s.sector_name,
                ss.stock_code,
                st."证券简称"
            FROM sector_stocks ss
            JOIN sectors s ON s.sector_id = ss.sector_id
            LEFT JOIN stocks st ON ss.stock_code = st."证券代码"
            LIMIT 10
        ''')
        
        stocks = cursor.fetchall()
        logger.info("\n成分股示例数据（前10条）：")
        for stock in stocks:
            logger.info(f"板块: {stock[0]}, 股票代码: {stock[1]}, 股票名称: {stock[2]}")
            
    except Exception as e:
        logger.error(f"检查板块数据失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def init_default_sectors():
    """初始化默认板块数据"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 插入默认板块
        default_sectors = [
            ('SZ50', '上证50', 'INDEX'),
            ('HS300', '沪深300', 'INDEX'),
            ('ZZ500', '中证500', 'INDEX')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO sectors (sector_code, sector_name, sector_type)
            VALUES (?, ?, ?)
        ''', default_sectors)
        
        conn.commit()
        logger.info("默认板块初始化完成")
        
    except Exception as e:
        logger.error(f"初始化默认板块失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
    check_sectors()
    init_default_sectors()  # 初始化默认板块