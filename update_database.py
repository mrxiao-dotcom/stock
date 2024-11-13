import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """更新数据库表结构"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 创建股票基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                "证券代码" TEXT PRIMARY KEY,
                "证券简称" TEXT,
                "证券类型" TEXT,
                "上市状态" TEXT,
                "上市日期" TEXT,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建股票行情数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT,
                trade_date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                pre_close REAL,
                change REAL,
                pct_chg REAL,
                vol REAL,
                amount REAL,
                adj_factor REAL,
                UNIQUE(ts_code, trade_date)
            )
        """)
        
        # 创建板块表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sectors (
                sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector_code TEXT UNIQUE NOT NULL,
                sector_name TEXT NOT NULL,
                sector_type TEXT NOT NULL,  -- INDEX(指数)、CUSTOM(自定义)
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建板块成分股关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sector_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
                UNIQUE(sector_id, stock_code)
            )
        """)
        
        # 插入默认指数板块数据
        default_sectors = [
            ('SZ50', '上证50', 'INDEX'),
            ('HS300', '沪深300', 'INDEX'),
            ('ZZ500', '中证500', 'INDEX')
        ]
        
        # 插入板块数据
        for sector_code, sector_name, sector_type in default_sectors:
            try:
                cursor.execute("""
                    INSERT INTO sectors (sector_code, sector_name, sector_type)
                    VALUES (?, ?, ?)
                    ON CONFLICT(sector_code) DO NOTHING
                """, (sector_code, sector_name, sector_type))
                logger.info(f"插入板块: {sector_name} ({sector_code})")
            except Exception as e:
                logger.error(f"插入板块 {sector_name} 失败: {str(e)}")
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_data_ts_code 
            ON stock_data(ts_code)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_data_trade_date 
            ON stock_data(trade_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sector_stocks_stock_code 
            ON sector_stocks(stock_code)
        """)
        
        conn.commit()
        logger.info("数据库结构更新完成")
        
        # 验证数据
        cursor.execute("SELECT sector_code, sector_name, sector_type FROM sectors")
        sectors = cursor.fetchall()
        logger.info("\n已插入的板块:")
        for sector in sectors:
            logger.info(f"- {sector[0]}: {sector[1]} ({sector[2]})")
        
        logger.info(f"\n共插入 {len(sectors)} 个板块")
        
    except Exception as e:
        logger.error(f"更新数据库结构时出错: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema() 