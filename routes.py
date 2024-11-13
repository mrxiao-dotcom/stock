from flask import jsonify, request
from . import data_updater

@app.route('/api/update_historical_data', methods=['POST'])
def update_historical_data():
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "请求必须是JSON格式"
            }), 400
            
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "status": "error",
                "message": "无法解析JSON数据"
            }), 400
            
        start_date = data.get('start_date', '2023-09-20')  # 默认起始日期
        end_date = data.get('end_date')
        
        if not end_date:
            from datetime import datetime
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        updater = data_updater.StockDataUpdater()
        result = updater.update_historical_data(start_date, end_date)
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"更新历史数据时发生错误: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"服务器错误: {str(e)}"
        }), 500