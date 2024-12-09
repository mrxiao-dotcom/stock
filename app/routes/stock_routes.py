from flask import jsonify
from app import app
from utils.database import get_mysql_connection
from utils.logger import setup_logger, log_error
import sys

logger = setup_logger('stock_routes')

@app.route('/api/stock/<string:stock_code>/detail')
def get_stock_detail(stock_code):
    """获取个股详情数据"""
    try:
        logger.info(f"获取股票 {stock_code} 的详细信息")
        
        # 标准化股票代码格式
        stock_code = stock_code.upper()  # 转换为大写
        if '.' not in stock_code:  # 如果没有后缀，根据股票代码添加后缀
            if stock_code.startswith('6'):
                stock_code += '.SH'
            elif stock_code.startswith(('0', '3')):
                stock_code += '.SZ'
        
        with get_mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # 先检查股票是否存在
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM stocks 
                WHERE 证券代码 = %s
            ''', (stock_code,))
            
            if cursor.fetchone()['count'] == 0:
                logger.warning(f"未找到股票: {stock_code}")
                return jsonify({
                    'success': False,
                    'message': f'未找到股票: {stock_code}'
                }), 404
            
            # 获取股票基本信息
            cursor.execute('''
                SELECT 证券代码 as code, 证券简称 as name
                FROM stocks 
                WHERE 证券代码 = %s
            ''', (stock_code,))
            
            stock_info = cursor.fetchone()

            # 获取股票历史数据
            try:
                cursor.execute('''
                    WITH DailyPrices AS (
                        SELECT 
                            trade_date,
                            open,
                            high,
                            low,
                            close,
                            amount,
                            LAG(close) OVER (ORDER BY trade_date) as prev_close
                        FROM stock_data
                        WHERE ts_code = %s
                        AND trade_date >= '20240920'
                        ORDER BY trade_date
                    )
                    SELECT 
                        trade_date,
                        open,
                        high,
                        low,
                        close,
                        amount,
                        prev_close,
                        CASE 
                            WHEN prev_close IS NOT NULL AND prev_close != 0 
                            THEN ((close - prev_close) / prev_close * 100)
                            ELSE 0 
                        END as change_pct
                    FROM DailyPrices
                    ORDER BY trade_date
                ''', (stock_code,))
            except Exception as e:
                log_error(logger, f"SQL查询失败: {str(e)}")
                raise

            price_data = cursor.fetchall()
            
            if not price_data:
                logger.warning(f"未找到股票 {stock_code} 的历史数据")
                return jsonify({
                    'success': False,
                    'message': f'未找到股票历史数据'
                }), 404

            # 获取所属板块
            cursor.execute('''
                SELECT 
                    s.sector_name,
                    s.sector_type
                FROM sectors s
                JOIN sector_stocks ss ON s.sector_id = ss.sector_id
                WHERE ss.stock_code = %s
                ORDER BY s.sector_type, s.sector_name
            ''', (stock_code,))
            
            sectors = cursor.fetchall()

            # 处理数据
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            changes = []
            super_large_inflow = []
            super_large_outflow = []
            large_inflow = []
            large_outflow = []
            net_inflow = []
            
            for row in price_data:
                # 格式化日期
                trade_date = f"{row['trade_date'][:4]}-{row['trade_date'][4:6]}-{row['trade_date'][6:]}"
                dates.append(trade_date)
                
                # 处理价格数据
                opens.append(float(row['open']) if row['open'] else 0)
                highs.append(float(row['high']) if row['high'] else 0)
                lows.append(float(row['low']) if row['low'] else 0)
                closes.append(float(row['close']) if row['close'] else 0)
                
                # 处理成交额（从千元转换为元）
                amount = float(row['amount']) * 1000 if row['amount'] else 0
                volumes.append(amount)
                
                # 处理涨跌幅
                change_pct = float(row['change_pct']) if row['change_pct'] is not None else 0
                changes.append(change_pct)
                
                # 生成资金流向数据
                money_flow = generate_money_flow(amount)
                super_large_inflow.append(money_flow['super_large_inflow'])
                super_large_outflow.append(money_flow['super_large_outflow'])
                large_inflow.append(money_flow['large_inflow'])
                large_outflow.append(money_flow['large_outflow'])
                net_inflow.append(money_flow['net_inflow'])

            logger.info(f"成功获取股票 {stock_code} 的详细信息")
            return jsonify({
                'success': True,
                'stock_data': {
                    'name': stock_info['name'],
                    'code': stock_info['code'],
                    'dates': dates,
                    'opens': opens,
                    'highs': highs,
                    'lows': lows,
                    'closes': closes,
                    'volumes': volumes,
                    'changes': changes,
                    'super_large_inflow': super_large_inflow,
                    'super_large_outflow': super_large_outflow,
                    'large_inflow': large_inflow,
                    'large_outflow': large_outflow,
                    'net_inflow': net_inflow
                },
                'sectors': sectors
            })
            
    except Exception as e:
        log_error(logger, f"获取股票详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"获取股票详情失败: {str(e)}"
        }), 500

    # 添加其他股票相关路由... 

# 在获取股票历史数据后，添加资金流向数据的模拟计算
def generate_money_flow(amount):
    """根据成交额生成资金流向数据"""
    import random
    base = amount * 0.01  # 基准金额为成交额的1%
    
    # 生成资金流向数据
    super_large_in = base * (0.8 + random.random() * 0.4)  # 80%-120%
    super_large_out = base * (0.8 + random.random() * 0.4)
    large_in = base * (0.6 + random.random() * 0.4)   # 60%-100%
    large_out = base * (0.6 + random.random() * 0.4)
    
    return {
        'super_large_inflow': round(super_large_in),
        'super_large_outflow': round(super_large_out),
        'large_inflow': round(large_in),
        'large_outflow': round(large_out),
        'net_inflow': round(super_large_in + large_in - super_large_out - large_out)
    } 