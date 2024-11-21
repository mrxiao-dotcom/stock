from flask import jsonify
from utils.logger import setup_logger
from utils.database import get_mysql_connection
from app.services.stock_analysis import StockAnalysis

logger = setup_logger('sector_routes')
stock_analysis = StockAnalysis()

def register_sector_routes(app):
    """注册板块相关路由"""
    
    @app.route('/api/sectors')
    def list_sectors():
        """获取所有板块信息"""
        try:
            logger.info("获取板块列表")
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute('''
                    SELECT 
                        s.sector_id,
                        s.sector_code,
                        s.sector_name,
                        s.sector_type,
                        COUNT(DISTINCT ss.stock_code) as stock_count
                    FROM sectors s
                    LEFT JOIN sector_stocks ss ON s.sector_id = ss.sector_id
                    GROUP BY 
                        s.sector_id, 
                        s.sector_code, 
                        s.sector_name, 
                        s.sector_type
                    ORDER BY s.sector_type, s.sector_name
                ''')
                
                sectors = cursor.fetchall()
                logger.info(f"查询到 {len(sectors)} 个板块")
                
                return jsonify({
                    'success': True,
                    'sectors': sectors
                })
                
        except Exception as e:
            error_msg = f"获取板块列表失败: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

    @app.route('/api/sector/<int:sector_id>/stocks')
    def get_sector_stock_data(sector_id):
        """获取板块内股票列表及其涨跌幅数据"""
        try:
            logger.info(f"获取板块 {sector_id} 的股票列表")
            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # 获取板块内的股票列表和基本信息，包括开盘价
                cursor.execute('''
                    SELECT DISTINCT
                        s.证券代码 as code,
                        s.证券简称 as name,
                        sd.open,
                        sd.close,
                        sd.amount,
                        sd.trade_date
                    FROM sector_stocks ss
                    JOIN stocks s ON ss.stock_code = s.证券代码
                    LEFT JOIN stock_data sd ON s.证券代码 = sd.ts_code
                    WHERE ss.sector_id = %s
                    AND sd.trade_date >= '20240920'
                    ORDER BY sd.trade_date
                ''', (sector_id,))
                
                price_data = cursor.fetchall()
                cursor.close()
                
                if not price_data:
                    return jsonify({
                        'success': True,
                        'daily_changes': {},
                        'dates': []
                    })
                
                # 处理数据
                daily_changes = {}
                dates = set()
                stock_names = {}  # 用于存储股票代码和名称的映射
                
                # 首先建立股票代码和名称的映射
                for row in price_data:
                    stock_names[row['code']] = row['name']
                
                for row in price_data:
                    trade_date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                    dates.add(trade_date)
                    
                    if trade_date not in daily_changes:
                        daily_changes[trade_date] = {
                            'stocks': [],
                            'total_amount': 0
                        }
                    
                    # 检查该股票是否已经在当天的列表中
                    stock_exists = any(s['code'] == row['code'] for s in daily_changes[trade_date]['stocks'])
                    if not stock_exists:
                        # 处理成交额（从千元转换为元）
                        amount = float(row['amount']) * 1000 if row['amount'] else 0
                        daily_changes[trade_date]['stocks'].append({
                            'code': row['code'],
                            'name': stock_names[row['code']],
                            'open': float(row['open']) if row['open'] else 0,
                            'close': float(row['close']) if row['close'] else 0,
                            'amount': amount,
                            'amount_str': f"{amount/100000000:.2f}亿" if amount >= 100000000 else f"{amount/10000:.2f}万"
                        })
                        daily_changes[trade_date]['total_amount'] = daily_changes[trade_date]['total_amount'] + amount
                
                # 计算每只股票相对于首日的涨跌幅
                sorted_dates = sorted(list(dates))
                first_date = sorted_dates[0]
                first_day_data = daily_changes[first_date]
                base_prices = {stock['code']: stock['open'] for stock in first_day_data['stocks']}  # 使用首日开盘价作为基准
                
                # 计算每天的涨跌幅
                for date in sorted_dates:
                    for stock in daily_changes[date]['stocks']:
                        base_price = base_prices.get(stock['code'])
                        if base_price and base_price != 0:
                            if date == first_date:  # 第一天使用当天收盘价相对开盘价的涨跌幅
                                stock['change'] = ((stock['close'] - stock['open']) / stock['open'] * 100)
                            else:  # 其他天使用收盘价相对首日开盘价的涨跌幅
                                stock['change'] = ((stock['close'] - base_price) / base_price * 100)
                        else:
                            stock['change'] = 0
                
                # 对每天的股票按涨跌幅排序
                for date_data in daily_changes.values():
                    date_data['stocks'].sort(key=lambda x: x['change'])  # 从小到大排序
                    amount = date_data['total_amount']
                    date_data['total_amount_str'] = f"{amount/100000000:.2f}亿" if amount >= 100000000 else f"{amount/10000:.2f}万"
                
                return jsonify({
                    'success': True,
                    'daily_changes': daily_changes,
                    'dates': sorted_dates
                })
                
        except Exception as e:
            error_msg = f"获取板块股票数据失败: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500

    # 添加其他板块相关路由... 