import tushare as ts
import sqlite3
import logging
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialDataUpdater:
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
        # 如果距离上次重置已经过了60秒，重置计数器
        if current_time - self.last_reset_time >= 60:
            self.request_count = 0
            self.last_reset_time = current_time
        
        # 如果已达到限制，等待到下一个时间窗口
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.last_reset_time)
            if wait_time > 0:
                logger.info(f"达到访问限制，等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
                self.request_count = 0
                self.last_reset_time = time.time()
        
        self.request_count += 1
        
    def get_report_date(self):
        """获取最近一期财报的日期"""
        current_date = datetime.now()
        current_year = current_date.year
        last_year = current_year - 1
        
        # 4月30日到5月1日获取去年年报
        if current_date.month == 4 and current_date.day >= 30:
            return f"{last_year}1231"
        if current_date.month == 5 and current_date.day == 1:
            return f"{last_year}1231"
            
        # 其他时间根据月份判断
        if current_date.month <= 4:  # 1-4月
            return f"{last_year}1231"  # 去年年报
        elif current_date.month <= 8:  # 5-8月
            if current_date.month <= 6:  # 5-6月
                return f"{current_year}0331"  # 今年一季报
            else:  # 7-8月
                return f"{current_year}0630"  # 今年半年报
        else:  # 9-12月
            return f"{current_year}0930"  # 今年三季报

    def update_financial_data(self):
        """更新财务数据"""
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            
            # 获取所有股票代码
            cursor.execute('SELECT DISTINCT "证券代码" FROM stocks')
            stock_codes = [row[0] for row in cursor.fetchall()]
            
            # 获取最近的报告期
            report_date = self.get_report_date()
            logger.info(f"获取 {report_date} 的财务数据")
            
            total = len(stock_codes)
            for i, ts_code in enumerate(stock_codes, 1):
                try:
                    logger.info(f"处理第 {i}/{total} 只股票: {ts_code}")
                    
                    # 获取资产负债表数据
                    self.check_rate_limit()
                    df_balance = self.pro.balancesheet(
                        ts_code=ts_code,
                        period=report_date,
                        fields=['ts_code', 'ann_date', 'end_date', 
                               'total_assets', 'total_liab', 'total_equity']
                    )
                    
                    # 获取利润表数据
                    self.check_rate_limit()
                    df_income = self.pro.income(
                        ts_code=ts_code,
                        period=report_date,
                        fields=['ts_code', 'ann_date', 'end_date',
                               'total_revenue', 'operate_profit', 'n_income']
                    )
                    
                    # 获取财务指标数据
                    self.check_rate_limit()
                    df_indicator = self.pro.fina_indicator(
                        ts_code=ts_code,
                        period=report_date,
                        fields=['ts_code', 'ann_date', 'end_date',
                               'grossprofit_margin', 'debt_to_assets']
                    )
                    
                    # 写入数据库
                    if not df_balance.empty:
                        df_balance.to_sql('balance_sheet', conn, if_exists='append', index=False)
                    
                    if not df_income.empty:
                        df_income.to_sql('income', conn, if_exists='append', index=False)
                    
                    if not df_indicator.empty:
                        df_indicator.to_sql('financial_indicator', conn, if_exists='append', index=False)
                    
                except Exception as e:
                    logger.error(f"处理股票 {ts_code} 时出错: {str(e)}")
                    continue
                
                # 每100只股票提交一次
                if i % 100 == 0:
                    conn.commit()
                    logger.info(f"已处理 {i} 只股票")
            
            conn.commit()
            logger.info("财务数据更新完成")
            
        except Exception as e:
            logger.error(f"更新财务数据失败: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def update_single_stock(self, ts_code):
        """更新单只股票的财务数据"""
        try:
            conn = sqlite3.connect('example.db')
            report_date = self.get_report_date()
            
            # 获取财务数据
            self.check_rate_limit()
            df_balance = self.pro.balancesheet(ts_code=ts_code, period=report_date)
            
            self.check_rate_limit()
            df_income = self.pro.income(ts_code=ts_code, period=report_date)
            
            self.check_rate_limit()
            df_indicator = self.pro.fina_indicator(ts_code=ts_code, period=report_date)
            
            # 写入数据库
            if not df_balance.empty:
                df_balance.to_sql('balance_sheet', conn, if_exists='append', index=False)
            
            if not df_income.empty:
                df_income.to_sql('income', conn, if_exists='append', index=False)
            
            if not df_indicator.empty:
                df_indicator.to_sql('financial_indicator', conn, if_exists='append', index=False)
            
            conn.commit()
            logger.info(f"股票 {ts_code} 的财务数据更新完成")
            
        except Exception as e:
            logger.error(f"更新股票 {ts_code} 的财务数据失败: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == '__main__':
    try:
        updater = FinancialDataUpdater()
        updater.update_financial_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")