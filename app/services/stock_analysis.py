from utils.logger import setup_logger
from utils.database import get_mysql_connection

logger = setup_logger('stock_analysis')

class StockAnalysis:
    def convert_stock_code(self, code):
        """转换股票代码格式
        sh.600001 -> 600001.SH
        sz.000001 -> 000001.SZ
        """
        if not code:
            return None
        try:
            market, number = code.split('.')
            if market.upper() == 'SH':
                return f"{number}.SH"
            elif market.upper() == 'SZ':
                return f"{number}.SZ"
            return None
        except:
            return None

    def get_daily_changes(self, sector_id):
        """获取板块内股票的每日涨幅数据"""
        try:
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # 获取板块内的股票列表
                cursor.execute('''
                    SELECT stock_code 
                    FROM sector_stocks 
                    WHERE sector_id = %s
                ''', (sector_id,))
                stocks = [row['stock_code'] for row in cursor.fetchall()]
                
                if not stocks:
                    return None
                    
                # 使用一个SQL查询获取所有股票的数据
                placeholders = ','.join(['%s' for _ in stocks])
                cursor.execute(f'''
                    WITH FirstPrices AS (
                        -- 获取每只股票的第一个交易日开盘价
                        SELECT ts_code, open as first_open
                        FROM stock_data sd1
                        WHERE ts_code IN ({placeholders})
                        AND trade_date = (
                            SELECT MIN(trade_date)
                            FROM stock_data sd2
                            WHERE sd2.ts_code = sd1.ts_code
                            AND trade_date >= '20240920'
                        )
                    ),
                    DailyData AS (
                        -- 获取每日数据
                        SELECT 
                            sd.trade_date,
                            sd.ts_code,
                            sd.close,
                            sd.amount,
                            fp.first_open
                        FROM stock_data sd
                        JOIN FirstPrices fp ON sd.ts_code = fp.ts_code
                        WHERE sd.ts_code IN ({placeholders})
                        AND sd.trade_date >= '20240920'
                    ),
                    DailyChanges AS (
                        -- 计算每日涨跌幅
                        SELECT 
                            trade_date,
                            ts_code,
                            ROUND(((close - first_open) / first_open * 100), 2) as total_change,
                            amount
                        FROM DailyData
                    ),
                    DailyTotals AS (
                        -- 计算每日总成交额
                        SELECT 
                            trade_date,
                            SUM(amount) as total_amount
                        FROM DailyData
                        GROUP BY trade_date
                    )
                    SELECT 
                        dc.trade_date,
                        dc.ts_code,
                        dc.total_change,
                        dc.amount,
                        dt.total_amount
                    FROM DailyChanges dc
                    JOIN DailyTotals dt ON dc.trade_date = dt.trade_date
                    ORDER BY dc.trade_date, dc.total_change
                ''', stocks + stocks)  # ��要两次stocks因为有两个IN子句
                
                rows = cursor.fetchall()
                
                # 处理查询结果
                daily_data = {}
                dates = set()
                current_date = None
                daily_stocks = []
                current_total_amount = 0
                
                for row in rows:
                    trade_date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                    stock_code = row['ts_code']
                    change = row['total_change']
                    amount = float(row['amount']) if row['amount'] is not None else 0
                    total_amount = float(row['total_amount']) if row['total_amount'] is not None else 0
                    
                    amount_wan = amount / 10
                    total_amount_wan = total_amount / 10
                    
                    if trade_date != current_date:
                        if current_date is not None:
                            daily_data[current_date] = {
                                'stocks': sorted(daily_stocks, key=lambda x: x['change']),
                                'total_amount': total_amount_wan,
                                'total_amount_str': f"{total_amount_wan/10000:.2f}亿" if total_amount_wan >= 10000 else f"{total_amount_wan:.2f}万"
                            }
                        current_date = trade_date
                        daily_stocks = []
                        current_total_amount = total_amount_wan
                        dates.add(trade_date)
                    
                    cursor.execute('SELECT 证券简称 FROM stocks WHERE 证券代码 = %s', (stock_code,))
                    stock_name = cursor.fetchone()
                    stock_name = stock_name['证券简称'] if stock_name else stock_code
                    
                    daily_stocks.append({
                        'code': stock_code,
                        'name': stock_name,
                        'change': change,
                        'amount': amount_wan,
                        'amount_str': f"{amount_wan/10000:.2f}亿" if amount_wan >= 10000 else f"{amount_wan:.2f}万"
                    })
                
                if current_date is not None:
                    daily_data[current_date] = {
                        'stocks': sorted(daily_stocks, key=lambda x: x['change']),
                        'total_amount': current_total_amount,
                        'total_amount_str': f"{current_total_amount/10000:.2f}亿" if current_total_amount >= 10000 else f"{current_total_amount:.2f}万"
                    }
                
                return {
                    'daily_data': daily_data,
                    'dates': sorted(list(dates))
                }
                
        except Exception as e:
            logger.error(f"获取每日涨幅数据失败: {str(e)}")
            return None

    def get_stock_daily_data(self, stock_code):
        """获取单个股票的每日涨幅和成交额数据"""
        try:
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # 获取股票名称
                cursor.execute('SELECT 证券简称 FROM stocks WHERE 证券代码 = %s', (stock_code,))
                stock_name = cursor.fetchone()
                
                if not stock_name:
                    logger.warning(f"未找到股票: {stock_code}")
                    return None
                
                # 获取股票数据
                cursor.execute('''
                    WITH DailyChanges AS (
                        SELECT 
                            trade_date,
                            close,
                            LAG(close) OVER (ORDER BY trade_date) as prev_close,
                            amount/10000 as amount
                        FROM stock_data
                        WHERE ts_code = %s
                        AND trade_date >= '20240920'
                        ORDER BY trade_date
                    )
                    SELECT 
                        trade_date,
                        CASE 
                            WHEN prev_close IS NOT NULL AND prev_close != 0 
                            THEN ROUND(((close - prev_close) / prev_close * 100), 2)
                            ELSE 0 
                        END as pct_chg,
                        amount
                    FROM DailyChanges
                    ORDER BY trade_date
                ''', (stock_code,))
                
                results = cursor.fetchall()
                
                if not results:
                    logger.warning(f"未找到股票数据: {stock_code}")
                    return None
                    
                formatted_data = {
                    'name': stock_name['证券简称'],
                    'dates': [],
                    'changes': [],
                    'volumes': []
                }
                
                for row in results:
                    date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                    formatted_data['dates'].append(date)
                    formatted_data['changes'].append(float(row['pct_chg']) if row['pct_chg'] is not None else 0)
                    formatted_data['volumes'].append(float(row['amount']) if row['amount'] is not None else 0)
                
                return formatted_data
                
        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            return None

    def get_stock_sectors(self, stock_code):
        """获取股票所属的板块列表"""
        try:
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute('''
                    SELECT s.sector_name, s.sector_type
                    FROM sectors s
                    JOIN sector_stocks ss ON s.sector_id = ss.sector_id
                    WHERE ss.stock_code = %s
                    ORDER BY s.sector_type, s.sector_name
                ''', (stock_code,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取股票所属板块失败: {str(e)}")
            return []