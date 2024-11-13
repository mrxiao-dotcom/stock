import tushare as ts
import sqlite3
import logging
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config.env')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundamentalUpdater:
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
            
            # 检查已有数据
            cursor.execute('''
                SELECT ts_code 
                FROM income 
                WHERE end_date = ?
            ''', (report_date,))
            existing_codes = {row[0] for row in cursor.fetchall()}
            
            # 过滤出需要更新的股票
            codes_to_update = [code for code in stock_codes if code not in existing_codes]
            
            if not codes_to_update:
                logger.info(f"{report_date} 的财务数据已是最新")
                return {
                    'success': True,
                    'message': '财务数据已是最新',
                    'count': 0
                }
            
            total = len(codes_to_update)
            updated = 0
            
            for i, ts_code in enumerate(codes_to_update, 1):
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
                    
                    # 去重处理
                    if not df_balance.empty:
                        df_balance = df_balance.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                        # 只保留需要的列
                        df_balance = df_balance[['ts_code', 'ann_date', 'end_date', 
                                               'total_assets', 'total_liab', 'total_equity']]
                    
                    if not df_income.empty:
                        df_income = df_income.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                        # 只保留需要的列
                        df_income = df_income[['ts_code', 'ann_date', 'end_date',
                                             'total_revenue', 'operate_profit', 'n_income']]
                    
                    if not df_indicator.empty:
                        df_indicator = df_indicator.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                        # 只保留需要的列
                        df_indicator = df_indicator[['ts_code', 'ann_date', 'end_date',
                                                   'grossprofit_margin', 'debt_to_assets']]
                    
                    # 检查数据有效性
                    if df_balance.empty and df_income.empty and df_indicator.empty:
                        logger.warning(f"股票 {ts_code} 未获取到任何财务数据")
                        continue
                    
                    # 写入数据库前再次检查是否存在
                    cursor.execute('''
                        SELECT COUNT(*) 
                        FROM income 
                        WHERE ts_code = ? AND end_date = ?
                    ''', (ts_code, report_date))
                    
                    if cursor.fetchone()[0] > 0:
                        logger.info(f"股票 {ts_code} 的数据已存在，跳过")
                        continue
                    
                    # 写入数据库
                    if not df_balance.empty:
                        df_balance.to_sql('balance_sheet', conn, if_exists='append', index=False)
                    
                    if not df_income.empty:
                        df_income.to_sql('income', conn, if_exists='append', index=False)
                    
                    if not df_indicator.empty:
                        df_indicator.to_sql('financial_indicator', conn, if_exists='append', index=False)
                    
                    updated += 1
                    logger.info(f"成功更新股票 {ts_code} 的财务数据")
                    
                except Exception as e:
                    logger.error(f"处理股票 {ts_code} 时出错: {str(e)}")
                    continue
                
                # 每100只股票提交一次
                if i % 100 == 0:
                    conn.commit()
                    logger.info(f"已处理 {i} 只股票")
            
            conn.commit()
            logger.info(f"财务数据更新完成，更新了 {updated} 只股票")
            
            return {
                'success': True,
                'message': f'成功更新 {updated} 只股票的财务数据',
                'count': updated
            }
            
        except Exception as e:
            error_msg = f"更新财务数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
            cursor = conn.cursor()
            
            # 检查数据是否已存在
            cursor.execute('''
                SELECT COUNT(*) 
                FROM daily_basic 
                WHERE trade_date = ?
            ''', (trade_date,))
            
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"{trade_date} 的每日指标数据已存在，跳过更新")
                return {
                    'success': True,
                    'message': f'{trade_date} 的数据已存在，无需更新',
                    'count': count
                }
            
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
                return {
                    'success': True,
                    'message': f'未获取到 {trade_date} 的数据',
                    'count': 0
                }
                
            # 写入数据库
            df.to_sql('daily_basic', conn, if_exists='append', index=False)
            
            conn.commit()
            logger.info(f"更新了 {len(df)} 条记录")
            
            return {
                'success': True,
                'message': f'成功更新 {len(df)} 条记录',
                'count': len(df)
            }
            
        except Exception as e:
            error_msg = f"更新每日指标数据失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
        updater = FundamentalUpdater()
        # 更新最新的每日指标数据
        updater.update_daily_basic()
        # 更新财务数据
        updater.update_financial_data()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}") 