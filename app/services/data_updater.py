from utils.logger import setup_logger
from utils.database import get_mysql_connection
import tushare as ts
import json
import os

logger = setup_logger('data_updater')

class StockDataUpdater:
    def __init__(self):
        self.pro = ts.pro_api()
        self.update_status = {
            'is_running': False,
            'progress': 0,
            'error_logs': [],
            'current_stock': None,
            'current_index': 0,
            'total_stocks': 0,
            'updated_count': 0,
            'status': 'idle'
        }
        
    def update_historical_data(self):
        """更新历史数据"""
        try:
            self.update_status['is_running'] = True
            self.update_status['status'] = 'running'
            self.update_status['error_logs'] = []
            
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # 获取所有股票列表
                cursor.execute('SELECT 证券代码, 证券简称 FROM stocks')
                stocks = cursor.fetchall()
                
                self.update_status['total_stocks'] = len(stocks)
                self.update_status['current_index'] = 0
                self.update_status['updated_count'] = 0
                
                for index, stock in enumerate(stocks):
                    try:
                        self.update_status['current_index'] = index + 1
                        self.update_status['current_stock'] = f"{stock['证券简称']}({stock['证券代码']})"
                        
                        # 获取历史数据
                        df = self.pro.daily(ts_code=stock['证券代码'], 
                                          start_date='20240920',
                                          fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
                        
                        if df is not None and not df.empty:
                            # 插入或更新数据
                            for _, row in df.iterrows():
                                cursor.execute('''
                                    INSERT INTO stock_data 
                                    (ts_code, trade_date, open, high, low, close, pre_close, 
                                     change, pct_chg, vol, amount)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON DUPLICATE KEY UPDATE
                                    open = VALUES(open),
                                    high = VALUES(high),
                                    low = VALUES(low),
                                    close = VALUES(close),
                                    pre_close = VALUES(pre_close),
                                    `change` = VALUES(`change`),
                                    pct_chg = VALUES(pct_chg),
                                    vol = VALUES(vol),
                                    amount = VALUES(amount)
                                ''', (
                                    row['ts_code'], row['trade_date'], row['open'], row['high'],
                                    row['low'], row['close'], row['pre_close'], row['change'],
                                    row['pct_chg'], row['vol'], row['amount']
                                ))
                            
                            conn.commit()
                            self.update_status['updated_count'] += 1
                            
                    except Exception as e:
                        error_msg = f"更新 {stock['证券简称']}({stock['证券代码']}) 失败: {str(e)}"
                        logger.error(error_msg)
                        self.update_status['error_logs'].append(error_msg)
                
            self.update_status['status'] = 'completed'
            logger.info("历史数据更新完成")
            return {'success': True, 'message': '更新完成'}
            
        except Exception as e:
            error_msg = f"更新历史数据失败: {str(e)}"
            logger.error(error_msg)
            self.update_status['status'] = 'error'
            self.update_status['error_logs'].append(error_msg)
            return {'success': False, 'message': error_msg}
            
        finally:
            self.update_status['is_running'] = False
            self._save_status()
    
    def get_update_progress(self):
        """获取更新进度"""
        return self.update_status
    
    def _save_status(self):
        """保存更新状态到文件"""
        try:
            with open('update_progress.json', 'w') as f:
                json.dump(self.update_status, f)
        except Exception as e:
            logger.error(f"保存更新状态失败: {str(e)}")