import tushare as ts
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

class StockUpdater:
    def __init__(self, db_path='example.db'):
        self.db_path = db_path
        self.ts_api = ts.pro_api('f27227e18d0ee9d6e0e2430dc1eca3e56e9ea70d0b3e24d72f72a174')  # 请替换为您的token
        
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
    
    def update_historical_data(self, start_date, progress_callback=None):
        """更新指定日期之后的所有股票行情数据"""
        conn = self.get_db_connection()
        try:
            # 获取所有股票代码
            stocks_df = pd.read_sql('SELECT "证券代码" as code FROM stocks', conn)
            
            for index, row in stocks_df.iterrows():
                stock_code = row['code']
                
                # 如果有回调函数，调用它报告进度
                if progress_callback:
                    for data in progress_callback(stock_code, index):
                        yield data
                
                # 检查最新数据日期
                latest_date = pd.read_sql(
                    'SELECT MAX(trade_date) as max_date FROM stock_data WHERE stock_code=?',
                    conn,
                    params=(stock_code,)
                )['max_date'].iloc[0]
                
                if latest_date is None:
                    latest_date = start_date
                else:
                    latest_date = (datetime.strptime(latest_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
                
                # 获取新数据
                df = self.ts_api.daily(ts_code=stock_code, start_date=latest_date)
                if df is not None and not df.empty:
                    df['stock_code'] = stock_code
                    df.to_sql('stock_data', conn, if_exists='append', index=False)
                    
                print(f"Updated {stock_code}")
                
        finally:
            conn.close()
    
    def save_sector_relation(self, stock_code, sector_name):
        """保存板块与个股的关系"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO stock_sectors (stock_code, sector_name)
                VALUES (?, ?)
            ''', (stock_code, sector_name))
            conn.commit()
        finally:
            conn.close()
    
    def batch_save_sector_relations(self, relations_data):
        """批量保存板块与个股的关系"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT OR IGNORE INTO stock_sectors (stock_code, sector_name)
                VALUES (?, ?)
            ''', relations_data)
            conn.commit()
        finally:
            conn.close() 