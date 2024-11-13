import tushare as ts
import sqlite3
import logging
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockBasicUpdater:
    def __init__(self):
        # 从环境变量获取token
        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            raise ValueError("未找到 TUSHARE_TOKEN 环境变量")
            
        self.pro = ts.pro_api(token)
        # Tushare API 访问限制：每分钟200次
        self.rate_limit = 200
        self.request_count = 0
        self.last_reset_time = time.time()
        
    def check_rate_limit(self):
        """检查并控制访问频率"""
        current_time = time.time()
        if current_time - self.last_reset_time >= 60:
            self.request_count = 0
            self.last_reset_time = current_time
        
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                logger.info(f"达到访问限制，等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
                self.request_count = 0
                self.last_reset_time = time.time()
        
        self.request_count += 1

    def init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            
            # 创建每日指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_basic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code VARCHAR(10) NOT NULL,       -- TS代码
                    trade_date VARCHAR(8) NOT NULL,     -- 交易日期
                    close DECIMAL(20,4),                -- 当日收盘价
                    turnover_rate DECIMAL(20,4),        -- 换手率（%）
                    turnover_rate_f DECIMAL(20,4),      -- 换手率（自由流通股）
                    volume_ratio DECIMAL(20,4),         -- 量比
                    pe DECIMAL(20,4),                   -- 市盈率（总市值/净利润， 亏损的PE为空）
                    pe_ttm DECIMAL(20,4),              -- 市盈率（TTM，亏损的PE为空）
                    pb DECIMAL(20,4),                   -- 市净率（总市值/净资产）
                    ps DECIMAL(20,4),                   -- 市销率
                    ps_ttm DECIMAL(20,4),              -- 市销率（TTM）
                    dv_ratio DECIMAL(20,4),            -- 股息率 （%）
                    dv_ttm DECIMAL(20,4),              -- 股息率（TTM）（%）
                    total_share DECIMAL(20,4),          -- 总股本 （万股）
                    float_share DECIMAL(20,4),          -- 流通股本 （万股）
                    free_share DECIMAL(20,4),          -- 自由流通股本 （万）
                    total_mv DECIMAL(20,4),            -- 总市值 （万元）
                    circ_mv DECIMAL(20,4),             -- 流通市值（万元）
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ts_code, trade_date)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_basic_code ON daily_basic(ts_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_basic_date ON daily_basic(trade_date)')
            
            conn.commit()
            logger.info("数据库表初始化完成")
            
        except Exception as e:
            logger.error(f"初始化数据库表失败: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def update_daily_basic(self, trade_date=None):
        """更新每日指标数据"""
        try:
            if trade_date is None:
                trade_date = time.strftime('%Y%m%d')
                
            logger.info(f"更新 {trade_date} 的每日指标数据")
            
            conn = sqlite3.connect('example.db')
            
            # 获取数据
            self.check_rate_limit()
            df = self.pro.daily_basic(trade_date=trade_date, fields=[
                'ts_code', 'trade_date', 'close', 'turnover_rate', 'turnover_rate_f',
                'volume_ratio', 'pe', 'pe_ttm', 'pb', 'ps', 'ps_ttm', 'dv_ratio',
                'dv_ttm', 'total_share', 'float_share', 'free_share', 'total_mv',
                'circ_mv'
            ])
            
            if df.empty:
                logger.warning(f"未获取到 {trade_date} 的数据")
                return
                
            # 写入数据库
            df.to_sql('daily_basic', conn, if_exists='append', index=False)
            
            conn.commit()
            logger.info(f"更新了 {len(df)} 条记录")
            
        except Exception as e:
            logger.error(f"更新每日指标数据失败: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == '__main__':
    try:
        updater = StockBasicUpdater()
        # 初始化数据库表
        updater.init_database()
        # 更新最新的每日指标数据
        updater.update_daily_basic('20241108')
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")