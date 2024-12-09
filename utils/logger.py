import logging
import os
import traceback
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name):
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 创建logs目录（如果不存在）
    os.makedirs('logs', exist_ok=True)

    # 文件处理器
    file_handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def log_error(logger, error_msg, exc_info=None):
    """记录错误信息，包括堆栈跟踪"""
    if exc_info:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.extract_tb(exc_traceback)
        # 获取最后一个堆栈帧（错误发生的位置）
        last_frame = tb[-1]
        error_location = f"{last_frame.filename}:{last_frame.lineno}"
        logger.error(f"{error_msg} at {error_location}\n{traceback.format_exc()}")
    else:
        logger.error(error_msg) 