from datetime import datetime, timedelta
import tushare as ts
import sqlite3
import logging
import time
import os
from dotenv import load_dotenv
import json

# 加载环境变量，指定配置文件名
load_dotenv('config.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataUpdater:
    _instance = None
    _status = {
        'is_running': False,
        'progress': 0,
        'error_logs': [],
        'current_stock': None,
        'current_index': 0,
        'total_stocks': 0,
        'updated_count': 0,
        'status': 'idle'  # idle, updating, success, error
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockDataUpdater, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = 'example.db'
            # 从环境变量获取token
            token = os.getenv('TUSHARE_TOKEN')
            if not token:
                raise ValueError("未找到 TUSHARE_TOKEN 环境变量")
            # 初始化tushare
            self.pro = ts.pro_api(token)
            # Tushare API 访问限制：每分钟200次
            self.rate_limit = 200
            self.request_count = 0
            self.last_reset_time = time.time()
            self.is_updating = False
            self.current_progress = 0
            self.call_count = 0
            self.last_call_time = time.time()
            self._init_db()
            self.initialized = True

    @classmethod
    def get_status(cls):
        return cls._status

    @classmethod
    def update_status(cls, **kwargs):
        cls._status.update(kwargs)
        # 确保进度是有效数字
        if 'progress' in kwargs:
            cls._status['progress'] = float(kwargs['progress'])
        logger.info(f"Status updated: {cls._status}")

    def _check_rate_limit(self):
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

    def _get_stock_data(self, code, start_date, end_date):
        """获取单只股票数据"""
        self._check_rate_limit()
        try:
            df = self.pro.daily(ts_code=code, 
                                 start_date=start_date.replace('-', ''), 
                                 end_date=end_date.replace('-', ''))
            return df
        except Exception as e:
            logger.error(f"获取股票 {code} 数据失败: {str(e)}")
            raise
    
    def _init_db(self):
        """初始化数据库表"""
        logger.info("初始化数据库...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建股票基本信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                "证券代码" TEXT PRIMARY KEY,
                "证券简称" TEXT,
                "证券类型" TEXT,
                "上市状态" TEXT,
                "上市日期" TEXT
            )
            ''')
            
            # 创建股票行情数据表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                trade_date TEXT,
                ts_code TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                vol REAL,
                amount REAL,
                UNIQUE(ts_code, trade_date)
            )
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_missing_dates(self, stock_code, start_date, end_date):
        """获取缺失的日期列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # 确保日期格式正确
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # 如果开始日期早于2024-09-20，则使用2024-09-20作为开始日期
            min_date = datetime.strptime('2024-09-20', '%Y-%m-%d')
            if start < min_date:
                start = min_date
                start_date = '2024-09-20'
            
            # 获取已有的日期列表
            cursor.execute('''
                SELECT trade_date 
                FROM stock_data 
                WHERE ts_code = ? 
                AND trade_date BETWEEN ? AND ?
                ORDER BY trade_date
            ''', (stock_code, start_date.replace('-', ''), end_date.replace('-', '')))
            
            existing_dates = set(row[0] for row in cursor.fetchall())
            
            # 生成完整的日期列表
            date_list = []
            current_date = start
            
            while current_date <= end:
                date_str = current_date.strftime('%Y%m%d')
                if date_str not in existing_dates:
                    date_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            return date_list
        finally:
            conn.close()
    
    def update_historical_data(self):
        """更新历史数据"""
        try:
            logger.info("开始更新历史数据...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有股票列表
            cursor.execute('SELECT "证券代码" FROM stocks')
            all_stocks = cursor.fetchall()
            
            # 过滤掉4、8和9开头的股票代码
            stock_list = [stock[0] for stock in all_stocks 
                         if stock[0] and not (stock[0].startswith(('4', '8', '9')))]
            
            total_stocks = len(stock_list)
            updated_count = 0
            error_logs = []
            
            logger.info(f"共有 {total_stocks} 只股票需要更新")
            
            # 获取最新交易日期
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = '20240920'  # 固定起始日期
            
            # 批量处理股票，每批50只
            batch_size = 50
            for i in range(0, len(stock_list), batch_size):
                batch_stocks = stock_list[i:i+batch_size]
                logger.info(f"正在处理第 {i+1}-{min(i+batch_size, total_stocks)} 只股票")
                
                for stock_code in batch_stocks:
                    try:
                        # 获取已有数据的最新日期
                        cursor.execute('''
                            SELECT MAX(trade_date) 
                            FROM stock_data 
                            WHERE ts_code = ?
                        ''', (stock_code,))
                        last_date = cursor.fetchone()[0]
                        
                        if last_date:
                            # 如果已有数据的最新日期等于或晚于起始日期，从最新日期的��二天开始更新
                            if last_date >= start_date:
                                query_start = str(int(last_date) + 1)
                            else:
                                query_start = start_date
                        else:
                            query_start = start_date
                        
                        logger.info(f"更新 {stock_code}, 开始日期: {query_start}")
                        
                        # 检查频率限制
                        self._check_rate_limit()
                        
                        # 获取数据
                        df = self.pro.daily(ts_code=stock_code,
                                             start_date=query_start,
                                             end_date=end_date)
                        
                        if df is not None and not df.empty:
                            # 转换数据并保存
                            data_list = df.to_dict('records')
                            cursor.executemany('''
                                INSERT OR REPLACE INTO stock_data 
                                (trade_date, ts_code, open, high, low, close, vol, amount)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', [(str(row['trade_date']), row['ts_code'],
                                  row['open'], row['high'], row['low'], row['close'],
                                  row['vol'], row['amount']) for row in data_list])
                            
                            conn.commit()
                            updated_count += 1
                            logger.info(f"成功更新 {stock_code}, 新增 {len(data_list)} 条数据")
                        else:
                            logger.info(f"{stock_code} 没有新数据需要更新")
                        
                    except Exception as e:
                        error_msg = f"更新 {stock_code} 失败: {str(e)}"
                        logger.error(error_msg)
                        error_logs.append(error_msg)
                        continue
                
                # 每批处理完后暂停1秒
                time.sleep(1)
            
            logger.info(f"更新完成，成功更新 {updated_count} 只股票，失败 {len(error_logs)} 只")
            return {
                'status': 'success',
                'updated_count': updated_count,
                'error_count': len(error_logs),
                'error_logs': error_logs
            }
            
        except Exception as e:
            error_msg = f"更新过程出错: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'message': error_msg
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _save_progress(self):
        """保存进度到文件"""
        with open('update_progress.json', 'w') as f:
            json.dump(self._status, f)
    
    def _validate_dates(self, start_date, end_date):
        """验证日期格式"""
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def pause_update(self):
        """暂停更新过程"""
        logger.info("正在暂停更新...")
        self.update_status(
            is_running=False,
            status='idle'
        )

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
                    self.current_progress = int(i * 100 / total)
                    
                    # 获取并更新单只股票数据
                    result = self.update_single_stock_financial(ts_code, report_date, conn)
                    if result:
                        updated += 1
                    
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
            self.current_progress = 0

    def update_single_stock_financial(self, ts_code, report_date=None, conn=None):
        """更新单只股票的财务数据"""
        try:
            if report_date is None:
                report_date = self.get_report_date()
                
            close_conn = False
            if conn is None:
                conn = sqlite3.connect('example.db')
                close_conn = True
            
            cursor = conn.cursor()
            
            # 检查数据是否已存在
            cursor.execute('''
                SELECT COUNT(*) 
                FROM balance_sheet 
                WHERE ts_code = ? AND end_date = ?
            ''', (ts_code, report_date))
            balance_exists = cursor.fetchone()[0] > 0
            
            cursor.execute('''
                SELECT COUNT(*) 
                FROM income 
                WHERE ts_code = ? AND end_date = ?
            ''', (ts_code, report_date))
            income_exists = cursor.fetchone()[0] > 0
            
            cursor.execute('''
                SELECT COUNT(*) 
                FROM financial_indicator 
                WHERE ts_code = ? AND end_date = ?
            ''', (ts_code, report_date))
            indicator_exists = cursor.fetchone()[0] > 0
            
            # 获取资产负债表数据
            self._check_rate_limit()
            df_balance = self.pro.balancesheet(
                ts_code=ts_code,
                period=report_date,
                fields=[
                    'ts_code', 'ann_date', 'end_date', 
                    'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int'
                ]
            )
            
            # 获取利润表数据
            self._check_rate_limit()
            df_income = self.pro.income(
                ts_code=ts_code,
                period=report_date,
                fields=[
                    'ts_code', 'ann_date', 'end_date',
                    'total_revenue', 'operate_profit', 'n_income_attr_p'
                ]
            )
            
            # 获取财务指标数据
            self._check_rate_limit()
            df_indicator = self.pro.fina_indicator(
                ts_code=ts_code,
                period=report_date,
                fields=[
                    'ts_code', 'ann_date', 'end_date',
                    'grossprofit_margin', 'debt_to_assets'
                ]
            )
            
            # 去重和列选择
            if not df_balance.empty:
                df_balance = df_balance.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                df_balance = df_balance.rename(columns={
                    'total_hldr_eqy_exc_min_int': 'total_equity'
                })
                df_balance = df_balance[['ts_code', 'ann_date', 'end_date', 
                                       'total_assets', 'total_liab', 'total_equity']]
                
                if balance_exists:
                    # 更新现有数据
                    for _, row in df_balance.iterrows():
                        cursor.execute('''
                            UPDATE balance_sheet 
                            SET total_assets = ?, 
                                total_liab = ?, 
                                total_equity = ?,
                                ann_date = ?,
                                update_time = CURRENT_TIMESTAMP
                            WHERE ts_code = ? AND end_date = ?
                        ''', (
                            row['total_assets'], 
                            row['total_liab'], 
                            row['total_equity'],
                            row['ann_date'],
                            row['ts_code'], 
                            row['end_date']
                        ))
                else:
                    # 插入新数据
                    df_balance.to_sql('balance_sheet', conn, if_exists='append', index=False)
            
            if not df_income.empty:
                df_income = df_income.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                df_income = df_income.rename(columns={
                    'n_income_attr_p': 'n_income'
                })
                df_income = df_income[['ts_code', 'ann_date', 'end_date',
                                     'total_revenue', 'operate_profit', 'n_income']]
                
                if income_exists:
                    # 更新现有数据
                    for _, row in df_income.iterrows():
                        cursor.execute('''
                            UPDATE income 
                            SET total_revenue = ?, 
                                operate_profit = ?, 
                                n_income = ?,
                                ann_date = ?,
                                update_time = CURRENT_TIMESTAMP
                            WHERE ts_code = ? AND end_date = ?
                        ''', (
                            row['total_revenue'], 
                            row['operate_profit'], 
                            row['n_income'],
                            row['ann_date'],
                            row['ts_code'], 
                            row['end_date']
                        ))
                else:
                    # 插入新数据
                    df_income.to_sql('income', conn, if_exists='append', index=False)
            
            if not df_indicator.empty:
                df_indicator = df_indicator.drop_duplicates(subset=['ts_code', 'end_date'], keep='first')
                df_indicator = df_indicator[['ts_code', 'ann_date', 'end_date',
                                           'grossprofit_margin', 'debt_to_assets']]
                
                if indicator_exists:
                    # 更新现有数据
                    for _, row in df_indicator.iterrows():
                        cursor.execute('''
                            UPDATE financial_indicator 
                            SET grossprofit_margin = ?, 
                                debt_to_assets = ?,
                                ann_date = ?,
                                update_time = CURRENT_TIMESTAMP
                            WHERE ts_code = ? AND end_date = ?
                        ''', (
                            row['grossprofit_margin'], 
                            row['debt_to_assets'],
                            row['ann_date'],
                            row['ts_code'], 
                            row['end_date']
                        ))
                else:
                    # 插入新数据
                    df_indicator.to_sql('financial_indicator', conn, if_exists='append', index=False)
            
            conn.commit()
            if close_conn:
                conn.close()
            
            logger.info(f"成功更新股票 {ts_code} 的财务数据")
            return True
            
        except Exception as e:
            logger.error(f"更新股票 {ts_code} 的财务数据失败: {str(e)}")
            return False

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
            self._check_rate_limit()
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

    def get_update_progress(self):
        """获取更新进度"""
        return {
            'is_updating': self.is_updating,
            'progress': self.current_progress
        }