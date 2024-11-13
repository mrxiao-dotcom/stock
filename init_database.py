import sqlite3
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute('''
        SELECT count(*) FROM sqlite_master 
        WHERE type='table' AND name=?
    ''', (table_name,))
    return cursor.fetchone()[0] > 0

def init_missing_tables():
    """只初始化缺失的表"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 检查并创建财务数据表 - 资产负债表
        if not check_table_exists(cursor, 'balance_sheet'):
            cursor.execute('''
                CREATE TABLE balance_sheet (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                    ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                    end_date VARCHAR(8) NOT NULL,      -- 报告期
                    total_assets DECIMAL(20,4),        -- 总资产
                    total_liab DECIMAL(20,4),          -- 总负债
                    total_equity DECIMAL(20,4),        -- 股东权益合计
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ts_code, end_date)
                )
            ''')
            logger.info("创建表: balance_sheet")
        
        # 检查并创建财务数据表 - 利润表
        if not check_table_exists(cursor, 'income'):
            cursor.execute('''
                CREATE TABLE income (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                    ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                    end_date VARCHAR(8) NOT NULL,      -- 报告期
                    total_revenue DECIMAL(20,4),       -- 营业总收入
                    operate_profit DECIMAL(20,4),      -- 营业利润
                    n_income DECIMAL(20,4),           -- 净利润
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ts_code, end_date)
                )
            ''')
            logger.info("创建表: income")
        
        # 检查并创建财务数据表 - 财务指标
        if not check_table_exists(cursor, 'financial_indicator'):
            cursor.execute('''
                CREATE TABLE financial_indicator (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                    ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                    end_date VARCHAR(8) NOT NULL,      -- 报告期
                    grossprofit_margin DECIMAL(20,4),  -- 毛利率
                    debt_to_assets DECIMAL(20,4),      -- 资产负债率
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ts_code, end_date)
                )
            ''')
            logger.info("创建表: financial_indicator")
        
        # 创建必要的索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_balance_sheet_code_date ON balance_sheet(ts_code, end_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_code_date ON income(ts_code, end_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_code_date ON financial_indicator(ts_code, end_date)')
        
        conn.commit()
        logger.info("缺失的数据库表初始化完成")
        
    except Exception as e:
        logger.error(f"初始化数据库表失败: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_missing_tables() 