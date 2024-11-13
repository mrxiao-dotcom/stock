import tushare as ts
import sqlite3
import logging
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFixer:
    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("未找到 TUSHARE_TOKEN 环境变量")
        self.ts_api = ts.pro_api(self.token)
        self.db_path = 'example.db'
        self.call_count = 0
        self.last_call_time = time.time()

    def _check_rate_limit(self):
        """检查并控制调用频率（每分钟最多200次）"""
        current_time = time.time()
        if current_time - self.last_call_time < 60:  # 一分钟内
            if self.call_count >= 190:  # 留一些余量
                sleep_time = 60 - (current_time - self.last_call_time)
                logger.info(f"达到调用限制，等待 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
                self.call_count = 0
                self.last_call_time = time.time()
        else:
            # 超过一分钟，重置计数器
            self.call_count = 0
            self.last_call_time = current_time
        
        self.call_count += 1

    def fix_sep20_data(self):
        """修复9月20日的数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. 获取需要修复的股票列表
            cursor.execute('''
                SELECT DISTINCT ts_code 
                FROM stock_data 
                WHERE trade_date = '20240920'
            ''')
            stocks = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"找到 {len(stocks)} 只股票需要修复")
            
            # 2. 遍历每只股票进行修复
            for idx, stock_code in enumerate(stocks, 1):
                try:
                    logger.info(f"正在修复 {stock_code} ({idx}/{len(stocks)})")
                    
                    # 检查频率限制
                    self._check_rate_limit()
                    
                    # 获取数据
                    df = self.ts_api.daily(ts_code=stock_code,
                                         start_date='20240920',
                                         end_date='20240920')
                    
                    if df is not None and not df.empty:
                        # 删除原有数据
                        cursor.execute('''
                            DELETE FROM stock_data 
                            WHERE ts_code = ? AND trade_date = '20240920'
                        ''', (stock_code,))
                        
                        # 插入新数据
                        data = df.iloc[0]
                        cursor.execute('''
                            INSERT INTO stock_data 
                            (trade_date, ts_code, open, high, low, close, vol, amount)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(data['trade_date']),
                            data['ts_code'],
                            data['open'],
                            data['high'],
                            data['low'],
                            data['close'],
                            data['vol'],
                            data['amount']
                        ))
                        
                        conn.commit()
                        logger.info(f"成功修复 {stock_code}")
                    else:
                        logger.warning(f"未获取到 {stock_code} 的数据")
                    
                except Exception as e:
                    logger.error(f"修复 {stock_code} 失败: {str(e)}")
                    continue
            
            # 3. 验证修复结果
            cursor.execute('''
                SELECT COUNT(*) 
                FROM stock_data 
                WHERE trade_date = '20240920'
            ''')
            fixed_count = cursor.fetchone()[0]
            logger.info(f"修复完成，共有 {fixed_count} 条记录")
            
        except Exception as e:
            logger.error(f"修复过程出错: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == '__main__':
    try:
        fixer = DataFixer()
        fixer.fix_sep20_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}") 