from app import create_app
from utils.logger import setup_logger

logger = setup_logger('main')

if __name__ == '__main__':
    try:
        app = create_app()
        logger.info("启动应用服务器")
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise 