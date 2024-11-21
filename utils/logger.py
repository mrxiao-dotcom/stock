import logging
from config.config import LOG_CONFIG
import os

_loggers = {}

def setup_logger(name):
    """创建或获取logger实例"""
    if name in _loggers:
        return _loggers[name]
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # 如果logger已经有处理器，直接返回
    if logger.handlers:
        return logger
        
    logger.setLevel(LOG_CONFIG['level'])
    
    # 文件处理器
    fh = logging.FileHandler(LOG_CONFIG['filename'])
    fh.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    
    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(LOG_CONFIG['format']))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    # 缓存logger实例
    _loggers[name] = logger
    
    return logger 