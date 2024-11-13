import sqlite3
import pandas as pd
from datetime import datetime
import logging

# 添加日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_stock_code(code):
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

def get_daily_changes(sector_id):
    """获取板块内股票的每日涨幅数据"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取板块内的股票列表
        cursor.execute('''
            SELECT stock_code 
            FROM sector_stocks 
            WHERE sector_id = ?
        ''', (sector_id,))
        stocks = [row[0] for row in cursor.fetchall()]
        
        if not stocks:
            return None
            
        # 使用一个SQL查询获取所有股票的数据
        placeholders = ','.join(['?' for _ in stocks])
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
                    sd.amount,  -- 保持原始单位（千元）
                    fp.first_open
                FROM stock_data sd
                JOIN FirstPrices fp ON sd.ts_code = fp.ts_code
                WHERE sd.ts_code IN ({placeholders})
                AND sd.trade_date >= '20240920'
            ),
            DailyChanges AS (
                -- 计算每日涨跌幅（相对于第一天开盘价）
                SELECT 
                    trade_date,
                    ts_code,
                    ROUND(((close - first_open) / first_open * 100), 2) as total_change,
                    amount  -- 单位：千元
                FROM DailyData
            ),
            DailyTotals AS (
                -- 计算每日总成交额（单位：千元）
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
        ''', stocks + stocks)  # 需要两次stocks因为有两个IN子句
        
        rows = cursor.fetchall()
        
        # 处理查询结果
        daily_data = {}
        dates = set()
        
        # 按日期处理数据
        current_date = None
        daily_stocks = []
        current_total_amount = 0
        
        for row in rows:
            trade_date = f"{row[0][:4]}-{row[0][4:6]}-{row[0][6:]}"
            stock_code = row[1]
            change = row[2]
            amount = float(row[3]) if row[3] is not None else 0  # 单位：千元
            total_amount = float(row[4]) if row[4] is not None else 0  # 单位：千元
            
            # 转换成交额单位
            amount_wan = amount / 10  # 转换为万元
            total_amount_wan = total_amount / 10  # 转换为万元
            
            # 如果是新的日期
            if trade_date != current_date:
                if current_date is not None:
                    # 保存前一天的数据
                    daily_data[current_date] = {
                        'stocks': sorted(daily_stocks, key=lambda x: x['change']),  # 按涨幅排序
                        'total_amount': total_amount_wan,  # 单位：万元
                        'total_amount_str': f"{total_amount_wan/10000:.2f}亿" if total_amount_wan >= 10000 else f"{total_amount_wan:.2f}万"
                    }
                # 重置新一天的数据
                current_date = trade_date
                daily_stocks = []
                current_total_amount = total_amount_wan
                dates.add(trade_date)
            
            # 获取股票名称
            cursor.execute('SELECT "证券简称" FROM stocks WHERE "证券代码" = ?', (stock_code,))
            stock_name = cursor.fetchone()
            stock_name = stock_name[0] if stock_name else stock_code
            
            # 添加股票数据
            daily_stocks.append({
                'code': stock_code,
                'name': stock_name,
                'change': change,
                'amount': amount_wan,  # 单位：万元
                'amount_str': f"{amount_wan/10000:.2f}亿" if amount_wan >= 10000 else f"{amount_wan:.2f}万"
            })
        
        # 保存最后一天的数据
        if current_date is not None:
            daily_data[current_date] = {
                'stocks': sorted(daily_stocks, key=lambda x: x['change']),  # 按涨幅排序
                'total_amount': current_total_amount,  # 单位：万元
                'total_amount_str': f"{current_total_amount/10000:.2f}亿" if current_total_amount >= 10000 else f"{current_total_amount:.2f}万"
            }
        
        return {
            'daily_data': daily_data,
            'dates': sorted(list(dates))
        }
        
    except Exception as e:
        logger.error(f"获取每日涨幅数据失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_stock_daily_data(stock_code):
    """获取单个股票的每日涨幅和成交额数据"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 转换股票代码格式（如果需要）
        ts_code = stock_code
        if '.' in stock_code:
            code, market = stock_code.split('.')
            if market.upper() == 'SH':
                ts_code = f"sh.{code}"
            elif market.upper() == 'SZ':
                ts_code = f"sz.{code}"
        
        # 获取股票名称
        cursor.execute('SELECT "证券简称" FROM stocks WHERE "证券代码" = ?', (ts_code,))
        stock_name = cursor.fetchone()
        
        if not stock_name:
            # 尝试使用原始代码再次查询
            cursor.execute('SELECT "证券简称" FROM stocks WHERE "证券代码" = ?', (stock_code,))
            stock_name = cursor.fetchone()
            if not stock_name:
                logger.warning(f"未找到股票: {stock_code}")
                return None
        
        # 获取股票数据，限制日期范围从2024-09-20开始
        cursor.execute('''
            WITH DailyChanges AS (
                SELECT 
                    trade_date,
                    close,
                    LAG(close) OVER (ORDER BY trade_date) as prev_close,
                    amount/10000 as amount  -- 转换为万元单位
                FROM stock_data
                WHERE (ts_code = ? OR ts_code = ?)
                AND trade_date >= '20240920'
                ORDER BY trade_date
            )
            SELECT 
                trade_date,
                CASE 
                    WHEN prev_close IS NOT NULL AND prev_close != 0 
                    THEN ROUND(((close - prev_close) / prev_close * 100), 2)  -- 保留2位小数
                    ELSE 0 
                END as pct_chg,
                amount
            FROM DailyChanges
            ORDER BY trade_date
        ''', (ts_code, stock_code))
        
        results = cursor.fetchall()
        
        if not results:
            logger.warning(f"未找到股票数据: {stock_code}")
            return None
            
        # 格式化数据用于两个独立的图表
        formatted_data = {
            'name': stock_name[0],
            'dates': [],  # 共用的日期轴
            'price_chart': {  # 涨跌幅图表数据
                'title': f'{stock_name[0]}涨跌幅(%)',
                'series': [{
                    'name': '涨跌幅',
                    'type': 'line',
                    'data': []
                }]
            },
            'volume_chart': {  # 成交额图表数据
                'title': f'{stock_name[0]}成交额(万元)',
                'series': [{
                    'name': '成交额',
                    'type': 'line',
                    'data': []
                }]
            }
        }
        
        for row in results:
            # 格式化日期为 YYYY-MM-DD
            date = f"{row[0][:4]}-{row[0][4:6]}-{row[0][6:]}"
            formatted_data['dates'].append(date)
            formatted_data['price_chart']['series'][0]['data'].append(
                round(float(row[1]), 2) if row[1] is not None else 0  # 涨跌幅
            )
            formatted_data['volume_chart']['series'][0]['data'].append(
                float(row[2]) if row[2] is not None else 0  # 成交额
            )
        
        return formatted_data
        
    except Exception as e:
        logger.error(f"获取股票数据失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_stock_sectors(stock_code):
    """获取股票所属的板块列表"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.sector_name, s.sector_type
            FROM sectors s
            JOIN sector_stocks ss ON s.sector_id = ss.sector_id
            WHERE ss.stock_code = ?
            ORDER BY s.sector_type, s.sector_name
        ''', (stock_code,))
        
        return [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
        
    except Exception as e:
        logger.error(f"获取股票所属板块失败: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()