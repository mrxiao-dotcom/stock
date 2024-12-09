import os
import sys
import logging
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'stock_db')
}

# SQL语句
CREATE_TABLES_SQL = """
-- 创建股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    证券代码 VARCHAR(20) PRIMARY KEY,
    证券简称 VARCHAR(50),
    上市日期 DATE,
    所属行业 VARCHAR(50),
    总股本 DECIMAL(20,2),
    流通股本 DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建股票日线数据表
CREATE TABLE IF NOT EXISTS stock_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20),
    trade_date VARCHAR(8),
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    vol DECIMAL(20,2),
    amount DECIMAL(20,2),
    change_pct DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ts_code_date (ts_code, trade_date)
);

-- 创建指数日线数据表
CREATE TABLE IF NOT EXISTS stock_index_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts_code VARCHAR(20),
    name VARCHAR(50),
    trade_date VARCHAR(8),
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    vol DECIMAL(20,2),
    amount DECIMAL(20,2),
    change_pct DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ts_code_date (ts_code, trade_date)
);

-- 创建板块表
CREATE TABLE IF NOT EXISTS sectors (
    sector_id INT AUTO_INCREMENT PRIMARY KEY,
    sector_name VARCHAR(50) NOT NULL,
    sector_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name_type (sector_name, sector_type)
);

-- 创建板块股票关系表
CREATE TABLE IF NOT EXISTS sector_stocks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sector_id INT,
    stock_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sector_stock (sector_id, stock_code),
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
    FOREIGN KEY (stock_code) REFERENCES stocks(证券代码)
);
"""

def init_database():
    """初始化数据库"""
    try:
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 执行建表语句
        for statement in CREATE_TABLES_SQL.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        logger.info('数据库初始化成功')
        
    except Exception as e:
        logger.error(f'数据库初始化失败: {str(e)}')
        raise
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_database() 