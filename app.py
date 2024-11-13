from flask import Flask, jsonify, request, render_template, send_from_directory, Response
from sector_updater import SectorUpdater
from stock_updater import StockUpdater
from stock_top20 import get_daily_changes, get_stock_daily_data, get_stock_sectors
from data_updater import StockDataUpdater
from fundamental_updater import FundamentalUpdater
import logging
import sqlite3
from werkzeug.serving import WSGIRequestHandler
import os
import time
import threading
import json
from datetime import datetime
import tushare as ts

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建应用实例，指定模板和静态文件目录
app = Flask(__name__,
            template_folder='templates',  # 指定模板目录
            static_folder='static')       # 指定静态文件目录

# 从环境变量或配置文件获取 token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '7e48b6886e59f9c5d6a6e23e6018e8c2c4f029c3c9c9f1f8c9c9f1f8')

# 初始化 tushare
try:
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    logger.info("Tushare API 初始化成功")
except Exception as e:
    logger.error(f"Tushare API 初始化失败: {str(e)}")
    raise

# 增加超时配置
app.config['TIMEOUT'] = 300  # 设置超时时间为300秒
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1年的缓存
app.config['PERMANENT_SESSION_LIFETIME'] = 300  # 5分钟会话时间

# 添加 CORS 支持
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# 添加响应头，禁用缓存
@app.after_request
def add_header(response):
    """添加响应头，禁用缓存"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 添加根路由
@app.route('/')
def index():
    """返回主页"""
    try:
        logger.info("访问主页")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"渲染主页失败: {str(e)}")
        return f"Error: {str(e)}", 500

# 添加静态文件由
@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    try:
        logger.info(f"请求静态文件: {filename}")
        return send_from_directory('static', filename)
    except Exception as e:
        logger.error(f"提供静态文件失败: {str(e)}")
        return f"Error: {str(e)}", 404

# 创建全局状态字典
update_status = {
    'is_running': False,
    'progress': 0,
    'error_logs': [],
    'current_stock': None,
    'current_index': 0,
    'total_stocks': 0,
    'updated_count': 0,
    'status': 'idle'  # idle, updating, success, error
}

# 数据更新相关路由
@app.route('/api/update_historical_data', methods=['POST'])
def update_historical_data():
    try:
        logger.info("1. 接收到更新请求")
        
        # 创建更新器实例
        updater = StockDataUpdater()
        
        # 执行更新
        result = updater.update_historical_data()
        
        return jsonify({
            'status': 'started',
            'message': '更新已启动'
        })
        
    except Exception as e:
        error_msg = f"更新失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

@app.route('/api/update_progress')
def get_update_progress():
    try:
        # 从文件读取进度
        if os.path.exists('update_progress.json'):
            with open('update_progress.json', 'r') as f:
                status = json.load(f)
        else:
            status = {
                'status': 'idle',
                'progress': 0,
                'is_running': False
            }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"获取进度失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stop_update', methods=['POST'])
def stop_update():
    try:
        # 从文件读取当前状态
        if os.path.exists('update_progress.json'):
            with open('update_progress.json', 'r') as f:
                status = json.load(f)
            
            # 更新状态
            status['is_running'] = False
            status['status'] = 'stopped'
            
            # 保存更新后的状态
            with open('update_progress.json', 'w') as f:
                json.dump(status, f)
        
        return jsonify({
            'success': True,
            'message': '更新已停'
        })
    except Exception as e:
        logger.error(f"停止更新失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 板块管理相关路由
@app.route('/api/save_sector_stocks', methods=['POST'])
def save_sector_stocks():
    try:
        data = request.get_json()
        sector_name = data.get('sector_name')
        stock_list = data.get('stock_list')
        
        if not sector_name or not stock_list:
            return jsonify({
                'success': False,
                'message': '板块名称和股票列表不能为空'
            }), 400
        
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        try:
            # 开始事务
            cursor.execute('BEGIN')
            
            # 处理股票列表（支持多种分隔符）
            stocks = []
            items = stock_list.replace('，', '#').replace(',', '#').replace('\n', '#').split('#')
            
            # 处理每个输入项（可能是代码或名称）
            for item in items:
                item = item.strip()
                if not item:
                    continue
                    
                # 尝试查找股票代码
                cursor.execute('''
                    SELECT "证券代码" 
                    FROM stocks 
                    WHERE "证券代码" = ? OR "证券简称" = ?
                ''', (item, item))
                result = cursor.fetchone()
                
                if result:
                    stocks.append(result[0])  # 使用查找到的股票代码
                else:
                    logger.warning(f"未找到股票: {item}")
            
            if not stocks:
                return jsonify({
                    'success': False,
                    'message': '未找到有效的股票代码'
                }), 400
            
            # 检查板块是否已存在
            cursor.execute('SELECT sector_id FROM sectors WHERE sector_name = ?', (sector_name,))
            result = cursor.fetchone()
            
            if result:
                # 板块已存在，更新成分股
                sector_id = result[0]
                # 清除原有成分股
                cursor.execute('DELETE FROM sector_stocks WHERE sector_id = ?', (sector_id,))
            else:
                # 生成板块代码
                sector_code = f"CUSTOM_{int(time.time())}"
                
                # 创建新板块
                cursor.execute('''
                    INSERT INTO sectors (sector_name, sector_code, sector_type) 
                    VALUES (?, ?, 'CUSTOM')
                ''', (sector_name, sector_code))
                sector_id = cursor.lastrowid
            
            # 插入成分股
            for stock_code in stocks:
                cursor.execute('''
                    INSERT INTO sector_stocks (sector_id, stock_code)
                    VALUES (?, ?)
                ''', (sector_id, stock_code))
            
            # 提交事务
            cursor.execute('COMMIT')
            
            logger.info(f"保存板块成功: {sector_name}, {len(stocks)} 只股票")
            
            return jsonify({
                'success': True,
                'message': f'成功保存板块 {sector_name}，包含 {len(stocks)} 只股票'
            })
            
        except Exception as e:
            # 回滚事务
            cursor.execute('ROLLBACK')
            raise
            
    except Exception as e:
        error_msg = f"保存板块失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/update_sector_stocks', methods=['POST'])
def update_sector_stocks():
    try:
        data = request.get_json()
        sector_code = data.get('sector_code')
        
        updater = SectorUpdater()
        result = updater.update_sector_stocks(sector_code)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"更新板块股票失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/rename_sector', methods=['POST'])
def rename_sector():
    try:
        data = request.get_json()
        sector_id = data.get('sector_id')
        new_name = data.get('new_name')
        
        updater = SectorUpdater()
        result = updater.rename_sector(sector_id, new_name)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"重命名板块失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/delete_sector', methods=['POST'])
def delete_sector():
    try:
        data = request.get_json()
        sector_id = data.get('sector_id')
        
        updater = SectorUpdater()
        result = updater.delete_sector(sector_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"删除板块失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# 数据浏览相关路由
@app.route('/api/get_sectors', methods=['GET'])
def get_sectors():
    """获取所有板块信息"""
    try:
        logger.info("获取板块列表")
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取所有板块信息和股票数量
        cursor.execute('''
            SELECT 
                s.sector_id,
                s.sector_code,
                s.sector_name,
                s.sector_type,
                COUNT(ss.stock_code) as stock_count
            FROM sectors s
            LEFT JOIN sector_stocks ss ON s.sector_id = ss.sector_id
            GROUP BY s.sector_id, s.sector_code, s.sector_name, s.sector_type
            ORDER BY s.sector_type, s.sector_name
        ''')
        
        sectors = [{
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'stock_count': row[4]
        } for row in cursor.fetchall()]
        
        logger.info(f"查询到 {len(sectors)} 个板块")
        
        return jsonify({
            'success': True,
            'sectors': sectors
        })
        
    except Exception as e:
        error_msg = f"获取板块列表失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/get_sector_stocks/<int:sector_id>')
def get_sector_stocks(sector_id):
    try:
        logger.info(f"获取板块 {sector_id} 的股票列表")
        # 获取块内股的每日涨幅数据
        data = get_daily_changes(sector_id)
        
        if not data:
            return jsonify({
                'success': False,
                'message': '未找到数据'
            }), 404
            
        return jsonify({
            'success': True,
            'daily_changes': data['daily_data'],
            'dates': data['dates']
        })
        
    except Exception as e:
        error_msg = f"获取板块股票数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/get_stock_detail/<string:stock_code>')
def get_stock_detail(stock_code):
    try:
        logger.info(f"获取股票 {stock_code} 的详细信息")
        # 获取个股详细数据
        stock_data = get_stock_daily_data(stock_code)
        sectors = get_stock_sectors(stock_code)
        
        if not stock_data:
            return jsonify({
                'success': False,
                'message': '未找到数据'
            }), 404
            
        return jsonify({
            'success': True,
            'stock_data': stock_data,
            'sectors': sectors
        })
        
    except Exception as e:
        error_msg = f"获取个股详情失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

# 获取板块信息列表
@app.route('/api/get_sector_info', methods=['GET'])
def get_sector_info():
    """获取板块信息列表（用于数据维护模块）"""
    try:
        logger.info("获取板块信息列表")
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取板块信息和股票数量
        cursor.execute('''
            SELECT 
                s.sector_id,
                s.sector_code,
                s.sector_name,
                s.sector_type,
                COUNT(ss.stock_code) as stock_count,
                s.update_time
            FROM sectors s
            LEFT JOIN sector_stocks ss ON s.sector_id = ss.sector_id
            GROUP BY s.sector_id, s.sector_code, s.sector_name, s.sector_type, s.update_time
            ORDER BY s.sector_type, s.sector_name
        ''')
        
        sectors = [{
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'type': row[3],
            'stock_count': row[4],
            'update_time': row[5]
        } for row in cursor.fetchall()]
        
        logger.info(f"查询到 {len(sectors)} 个板块")
        
        return jsonify({
            'success': True,
            'sectors': sectors
        })
        
    except Exception as e:
        error_msg = f"获取板块信息失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

# 获取板块成分股
@app.route('/api/get_sector_stocks_with_change/<int:sector_id>')
def get_sector_stocks_with_change(sector_id):
    """获取板块成分股列表（包含累计涨跌幅、成交额和当日行情）"""
    try:
        logger.info(f"获取板块 {sector_id} 的成分股列表")
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取板块名称
        cursor.execute('SELECT sector_name FROM sectors WHERE sector_id = ?', (sector_id,))
        sector_name = cursor.fetchone()
        
        if not sector_name:
            return jsonify({
                'success': False,
                'message': '未找到板块信息'
            }), 404
            
        # 获取所有交易日期
        cursor.execute('''
            SELECT DISTINCT trade_date
            FROM stock_data
            WHERE trade_date >= '20240920'
            ORDER BY trade_date
        ''')
        dates = [row[0] for row in cursor.fetchall()]
        
        # 获取板块成分股的第一天开盘价和每日数据
        cursor.execute('''
            WITH FirstPrices AS (
                -- 获取每只股的第一个交易日开盘价
                SELECT 
                    ts_code,
                    open as first_open
                FROM stock_data sd1
                WHERE trade_date = (
                    SELECT MIN(trade_date)
                    FROM stock_data sd2
                    WHERE sd2.ts_code = sd1.ts_code
                    AND trade_date >= '20240920'
                )
                AND ts_code IN (
                    SELECT stock_code 
                    FROM sector_stocks 
                    WHERE sector_id = ?
                )
            ),
            LatestData AS (
                -- 获取最新交易日数据
                SELECT 
                    ts_code,
                    trade_date,
                    open,
                    high,
                    low,
                    close,
                    vol,
                    amount,
                    "涨跌幅" as day_change
                FROM stock_data sd1
                WHERE trade_date = (
                    SELECT MAX(trade_date)
                    FROM stock_data
                )
            )
            SELECT 
                sd.trade_date,
                sd.ts_code,
                s."证券简称",
                sd.close,
                sd.amount,
                fp.first_open,
                ld.open as latest_open,
                ld.high as latest_high,
                ld.low as latest_low,
                ld.close as latest_close,
                ld.vol as latest_vol,
                ld.amount as latest_amount,
                ld.day_change as latest_change
            FROM stock_data sd
            JOIN FirstPrices fp ON sd.ts_code = fp.ts_code
            JOIN stocks s ON sd.ts_code = s."证券代码"
            LEFT JOIN LatestData ld ON sd.ts_code = ld.ts_code
            WHERE sd.ts_code IN (
                SELECT stock_code 
                FROM sector_stocks 
                WHERE sector_id = ?
            )
            AND sd.trade_date >= '20240920'
            ORDER BY sd.trade_date, sd.ts_code
        ''', (sector_id, sector_id))
        
        # 处理数据
        daily_changes = {}
        latest_stocks = []  # 存储最新一日的个股详细信息
        
        for row in cursor.fetchall():
            (date, code, name, close, amount, first_open, 
             latest_open, latest_high, latest_low, latest_close, 
             latest_vol, latest_amount, latest_change) = row
            
            # 计算相对于第一天开盘价的涨跌幅
            change = ((close - first_open) / first_open * 100) if first_open else None
            amount = float(amount) if amount else 0
            
            if date not in daily_changes:
                daily_changes[date] = {
                    'stocks': [],
                    'total_amount': 0
                }
            
            daily_changes[date]['stocks'].append({
                'code': code,
                'name': name,
                'change': round(change, 2) if change is not None else None
            })
            daily_changes[date]['total_amount'] += amount
            
            # 收集最新一日的个股详细信息
            if date == dates[-1]:
                latest_stocks.append({
                    'code': code,
                    'name': name,
                    'change': round(change, 2) if change is not None else None,
                    'latest_open': latest_open,
                    'latest_high': latest_high,
                    'latest_low': latest_low,
                    'latest_close': latest_close,
                    'latest_vol': latest_vol,
                    'latest_amount': latest_amount / 100000 if latest_amount else None,  # 转换为亿元
                    'latest_change': latest_change
                })
        
        # 对每天的数据进行处理
        for date in daily_changes:
            # 按涨跌幅排序
            daily_changes[date]['stocks'].sort(key=lambda x: x['change'] if x['change'] is not None else float('-inf'))
            
            # 转换成交额单位（千元转亿元）
            total_amount = daily_changes[date]['total_amount'] / 100000
            daily_changes[date]['total_amount'] = total_amount
            daily_changes[date]['total_amount_str'] = f"{total_amount:.2f}亿"
        
        logger.info(f"处理完成 {len(dates)} 天的数据，包含 {len(latest_stocks)} 只个股")
        
        return jsonify({
            'success': True,
            'sector_name': sector_name[0],
            'dates': dates,
            'daily_changes': daily_changes,
            'latest_stocks': latest_stocks  # 添���最新一日的个股详细信息
        })
        
    except Exception as e:
        error_msg = f"获取成分股列表失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/get_sector_members/<int:sector_id>', methods=['GET'])
def get_sector_members(sector_id):
    """获取板块成分股列表（用于数据维护模块）"""
    try:
        logger.info(f"获取板块 {sector_id} 的成分股列表")
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取板块名称
        cursor.execute('SELECT sector_name FROM sectors WHERE sector_id = ?', (sector_id,))
        sector_name = cursor.fetchone()
        
        if not sector_name:
            logger.warning(f"未找到板块信息: {sector_id}")
            return jsonify({
                'success': False,
                'message': '未找到板块信息'
            }), 404
            
        # 获取成分股列表
        cursor.execute('''
            SELECT 
                ss.stock_code,
                s."证券简称" as stock_name
            FROM sector_stocks ss
            LEFT JOIN stocks s ON ss.stock_code = s."证券代码"
            WHERE ss.sector_id = ?
            ORDER BY ss.stock_code
        ''', (sector_id,))
        
        stocks = [{
            'code': row[0],
            'name': row[1] if row[1] else row[0]
        } for row in cursor.fetchall()]
        
        logger.info(f"查询到 {len(stocks)} 只股票")
        
        return jsonify({
            'success': True,
            'sector_name': sector_name[0],
            'stocks': stocks
        })
        
    except Exception as e:
        error_msg = f"获取成分股列表失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/get_money_flow/<string:stock_code>')
def get_money_flow(stock_code):
    """获取个股资金流向数据"""
    try:
        logger.info(f"获取个股资金流向数据: {stock_code}")
        
        # 调用tushare接口获取资金流向数据
        df = pro.query('moneyflow', 
                      ts_code=stock_code,
                      start_date='20240920',
                      fields=[
                          'trade_date',
                          'buy_sm_vol', 'sell_sm_vol',   # 小单
                          'buy_md_vol', 'sell_md_vol',   # 中单
                          'buy_lg_vol', 'sell_lg_vol',   # 大单
                          'buy_elg_vol', 'sell_elg_vol', # 特大单
                          'net_mf_vol'                   # 净流入
                      ])
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'message': '未找到资金流向数据'
            }), 404
            
        # 按日期升序排序
        df = df.sort_values('trade_date')
        
        # 准备返回数据
        dates = df['trade_date'].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}").tolist()
        
        result = {
            'success': True,
            'dates': dates,
            'buy_sm_vol': df['buy_sm_vol'].tolist(),    # 小单买入量
            'sell_sm_vol': df['sell_sm_vol'].tolist(),  # 小单卖出量
            'buy_md_vol': df['buy_md_vol'].tolist(),    # 中单买入量
            'sell_md_vol': df['sell_md_vol'].tolist(),  # 中单卖出量
            'buy_lg_vol': df['buy_lg_vol'].tolist(),    # 大单买入量
            'sell_lg_vol': df['sell_lg_vol'].tolist(),  # 大单卖出量
            'buy_elg_vol': df['buy_elg_vol'].tolist(),  # 特大单买量
            'sell_elg_vol': df['sell_elg_vol'].tolist(),# 特大单卖出量
            'net_mf_vol': df['net_mf_vol'].tolist()     # 净流入量
        }
        
        logger.info(f"获取到 {len(dates)} 天的资金流向数据")
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"获取资金流向数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/get_sector_details/<int:sector_id>')
def get_sector_details(sector_id):
    """获取板块成分股详细信息"""
    try:
        logger.info(f"获取板块 {sector_id} 的成分股详细信息")
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 获取板块名称
        cursor.execute('SELECT sector_name FROM sectors WHERE sector_id = ?', (sector_id,))
        sector_name_row = cursor.fetchone()
        if not sector_name_row:
            return jsonify({
                'success': False,
                'message': '未找到板块信息'
            }), 404
            
        sector_name = sector_name_row[0]
        
        # 确定要获取的财报期
        report_date = get_report_date()
        logger.info(f"使用财报日期: {report_date}")
        
        # 获取板块成分股信息
        cursor.execute('''
            WITH LatestDaily AS (
                -- 获取最新每日指标数据
                SELECT 
                    ts_code,
                    total_mv,  -- 总市值（万元）
                    trade_date
                FROM daily_basic db1
                WHERE trade_date = (
                    SELECT MAX(trade_date)
                    FROM daily_basic db2
                    WHERE db2.ts_code = db1.ts_code
                )
            ),
            FinancialData AS (
                -- 获取最新财报数据
                SELECT 
                    i.ts_code,
                    i.total_revenue,
                    i.n_income as n_income_attr_p,
                    f.grossprofit_margin,
                    f.debt_to_assets
                FROM income i
                JOIN financial_indicator f ON i.ts_code = f.ts_code 
                    AND i.end_date = f.end_date
                WHERE i.end_date = ?
            )
            SELECT 
                ss.stock_code,
                s."证券简称" as stock_name,
                ld.total_mv / 10000 as total_market_value,  -- 转换为亿元
                fd.total_revenue,
                fd.n_income_attr_p,
                fd.grossprofit_margin,
                fd.debt_to_assets,
                ld.trade_date as price_date
            FROM sector_stocks ss
            JOIN stocks s ON ss.stock_code = s."证券代码"
            LEFT JOIN LatestDaily ld ON ss.stock_code = ld.ts_code
            LEFT JOIN FinancialData fd ON ss.stock_code = fd.ts_code
            WHERE ss.sector_id = ?
            ORDER BY total_market_value DESC NULLS LAST
        ''', (report_date, sector_id))
        
        stocks = [{
            'code': row[0],
            'name': row[1],
            'market_value': round(float(row[2]), 2) if row[2] else None,  # 已经是亿元
            'revenue': round(float(row[3])/100000000, 2) if row[3] else None,       # 转换为亿元
            'net_profit': round(float(row[4])/100000000, 2) if row[4] else None,    # 转换为亿元
            'gross_margin': round(float(row[5]), 2) if row[5] else None,            # 毛利率
            'debt_ratio': round(float(row[6]), 2) if row[6] else None               # 负债率
        } for row in cursor.fetchall()]
        
        logger.info(f"查询到 {len(stocks)} 只股票的详细信息")
        
        return jsonify({
            'success': True,
            'sector_name': sector_name,  # 添加板块名称
            'stocks': stocks,
            'report_date': report_date
        })
        
    except Exception as e:
        error_msg = f"获取成分股详细信息失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

def create_financial_tables():
    """创建财务数据相关的表"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 创建资负债表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                end_date VARCHAR(8) NOT NULL,      -- 报告期
                total_assets DECIMAL(20,4),        -- 总资产
                total_liab DECIMAL(20,4),          -- 总负债
                total_equity DECIMAL(20,4),        -- 股东权益合计
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建利润表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                end_date VARCHAR(8) NOT NULL,      -- 报告期
                total_revenue DECIMAL(20,4),       -- 营业总收入
                operate_profit DECIMAL(20,4),      -- 营业利润
                n_income DECIMAL(20,4),           -- 净利润
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建财务指标数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_indicator (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code VARCHAR(10) NOT NULL,      -- 股票代码
                ann_date VARCHAR(8) NOT NULL,      -- 公告日期
                end_date VARCHAR(8) NOT NULL,      -- 报告期
                grossprofit_margin DECIMAL(20,4),  -- 毛利率
                debt_to_assets DECIMAL(20,4),      -- 资产负债率
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("财务数据表创建成功")
        
    except Exception as e:
        logger.error(f"创建财务数据表失败: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_report_date():
    """获取最近一期财报的日期"""
    current_date = datetime.now()
    current_year = current_date.year
    last_year = current_year - 1
    
    # 4月30日到5月1日获取去年年报
    if current_date.month == 4 and current_date.day >= 30:
        return f"{last_year}1231"
    if current_date.month == 5 and current_date.day == 1:
        return f"{last_year}1231"
        
    # 他时间根据月份判断
    if current_date.month <= 4:  # 1-4月
        return f"{last_year}1231"  # 去年年报
    elif current_date.month <= 8:  # 5-8月
        if current_date.month <= 6:  # 5-6月
            return f"{current_year}0331"  # 今年一季报
        else:  # 7-8月
            return f"{current_year}0630"  # 今年半年报
    else:  # 9-12月
        return f"{current_year}0930"  # 今年三季报

def update_financial_data(stock_code):
    """更新指定股票的财务数据"""
    try:
        # 获取最近一期财报日期
        report_date = get_report_date()
        
        # 查询资产负债表数据
        df_balance = pro.balancesheet(ts_code=stock_code, 
                                    period=report_date,
                                    fields=['ts_code', 'ann_date', 'end_date', 
                                           'total_assets', 'total_liab', 'total_equity'])
        
        # 查询利润表数据
        df_income = pro.income(ts_code=stock_code,
                             period=report_date,
                             fields=['ts_code', 'ann_date', 'end_date',
                                    'total_revenue', 'operate_profit', 'n_income'])
        
        # 查财务指标数据
        df_indicator = pro.fina_indicator(ts_code=stock_code,
                                        period=report_date,
                                        fields=['ts_code', 'ann_date', 'end_date',
                                               'grossprofit_margin', 'debt_to_assets'])
        
        # 写入数据库
        conn = sqlite3.connect('example.db')
        
        if not df_balance.empty:
            df_balance.to_sql('balance_sheet', conn, if_exists='append', index=False)
            
        if not df_income.empty:
            df_income.to_sql('income', conn, if_exists='append', index=False)
            
        if not df_indicator.empty:
            df_indicator.to_sql('financial_indicator', conn, if_exists='append', index=False)
            
        conn.commit()
        logger.info(f"股票 {stock_code} 的财务数据更新成功")
        
    except Exception as e:
        logger.error(f"更新财务数据失败: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/get_financial_data/<string:stock_code>')
def get_financial_data(stock_code):
    """获取股票的财务数据"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        # 检查数据库中是否有数据
        cursor.execute('''
            SELECT COUNT(*) FROM balance_sheet 
            WHERE ts_code = ? AND end_date = ?
        ''', (stock_code, get_report_date()))
        
        if cursor.fetchone()[0] == 0:
            # 如果没有数据，从tushare获取
            update_financial_data(stock_code)
        
        # 查询最新财务数据
        cursor.execute('''
            SELECT 
                b.end_date,
                b.total_assets/100000000 as total_assets,
                b.total_liab/100000000 as total_liab,
                i.total_revenue/100000000 as total_revenue,
                i.n_income/100000000 as net_profit,
                f.grossprofit_margin,
                f.debt_to_assets
            FROM balance_sheet b
            JOIN income i ON b.ts_code = i.ts_code AND b.end_date = i.end_date
            JOIN financial_indicator f ON b.ts_code = f.ts_code AND b.end_date = f.end_date
            WHERE b.ts_code = ?
            ORDER BY b.end_date DESC
            LIMIT 1
        ''', (stock_code,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({
                'success': False,
                'message': '未找到财务数据'
            }), 404
            
        result = {
            'success': True,
            'end_date': row[0],
            'total_assets': row[1],  # 总资产(亿元)
            'total_liab': row[2],    # 总负债(亿元)
            'total_revenue': row[3],  # 营业收入(亿元)
            'net_profit': row[4],     # 净利润(亿元)
            'gross_margin': row[5],   # 毛利率(%)
            'debt_ratio': row[6]      # 资产负债率(%)
        }
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"获取财务数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

# 初始化数据更新器
data_updater = StockDataUpdater()

# 基本面据更新相关路由
@app.route('/api/update_financial_data', methods=['POST'])
def update_financial_data():
    """更新所有股票的财务数据"""
    try:
        logger.info("开始更新财务数据")
        result = data_updater.update_financial_data()
        return jsonify(result)
    except Exception as e:
        error_msg = f"更新财务数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/update_single_stock/<string:stock_code>', methods=['POST'])
def update_single_stock_financial(stock_code):
    """更新单只股票的财务数据"""
    try:
        logger.info(f"更新股票 {stock_code} 的财务数据")
        success = data_updater.update_single_stock_financial(stock_code)
        if success:
            return jsonify({
                'success': True,
                'message': f'股票 {stock_code} 的财务数据更新完成'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'股票 {stock_code} 的财务数据更新失败'
            }), 500
    except Exception as e:
        error_msg = f"更新股票数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/update_daily_basic', methods=['POST'])
@app.route('/api/update_daily_basic/<string:trade_date>', methods=['POST'])
def update_daily_basic_data(trade_date=None):
    """更新每日指标数据"""
    try:
        if trade_date:
            logger.info(f"更新 {trade_date} 的每日指标数据")
        else:
            logger.info("更新最新的每日指标数据")
            
        result = data_updater.update_daily_basic(trade_date)
        return jsonify(result)
    except Exception as e:
        error_msg = f"更新每日指标数据失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/update_progress')
def get_fundamental_update_progress():
    """获取更新进度"""
    return jsonify(data_updater.get_update_progress())

@app.context_processor
def utility_processor():
    def get_version():
        return datetime.now().strftime("%Y%m%d%H%M%S")
    return dict(version=get_version)


if __name__ == '__main__':
    try:
        # 确保必要的目录存在
        os.makedirs('static', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        
        # 启动应用
        logger.info("启动应用服务器")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise