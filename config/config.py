import os

# MySQL配置
MYSQL_CONFIG = {
    'host': '10.17.31.104',
    'user': 'root',
    'password': 'Xj774913@',
    'port': 3306,
    'database': 'stock',
    'charset': 'utf8mb4'
}

# Tushare配置
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '7e48b6886e59f9c5d6a6e23e6018e8c2c4f029c3c9c9f1f8c9c9f1f8')

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'logs/app.log'
}

# 其他配置
APP_CONFIG = {
    'DEBUG': True,
    'HOST': '127.0.0.1',
    'PORT': 5000
} 