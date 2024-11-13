from flask import Flask, jsonify, request, render_template, send_from_directory
import tushare as ts
import sqlite3
import logging
from datetime import datetime
import time
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataUpdater:
    def __init__(self):
        self.is_running = False
        self.progress = 0
        self.error_logs = []
        self.db_path = 'example.db'
        # 初始化tushare
        self.ts_api = ts.pro_api('f27227e18d0ee9d6e0e2430dc1eca3e56e9ea70d0b3e24d72f72a174')
        self.call_count = 0
        self.last_call_time = time.time()
        self._init_db()

    def _check_rate_limit(self):
        """检查并控制调用频率"""
        current_time = time.time()
        if current_time - self.last_call_time < 60 and self.call_count >= 500:
            sleep_time = 60 - (current_time - self.last_call_time)
            logger.info(f"达到调用限制，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            self.call_count = 0
            self.last_call_time = time.time()
        elif current_time - self.last_call_time >= 60:
            self.call_count = 0
            self.last_call_time = current_time
        self.call_count += 1

    def _init_db(self):
        """初始化数据库表"""
        logger.info("初始化数据库...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 创建股票基本信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                "证券代码" TEXT PRIMARY KEY,
                "证券简称" TEXT,
                "证券类型" TEXT,
                "上市状态" TEXT,
                "上市日期" TEXT
            )
            ''')

            # 创建股票行情数据表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT,
                trade_date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                pre_close REAL,
                change REAL,
                pct_chg REAL,
                vol REAL,
                amount REAL,
                adj_factor REAL,
                UNIQUE(ts_code, trade_date)
            )
            ''')

            # 创建板块表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sectors (
                sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector_code TEXT UNIQUE,
                sector_name TEXT NOT NULL,
                sector_type TEXT NOT NULL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建板块成分股关系表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sector_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector_id INTEGER NOT NULL,
                stock_code TEXT NOT NULL,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
                UNIQUE(sector_id, stock_code)
            )
            ''')

            conn.commit()
            logger.info("数据库初始化完成")

        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
        finally:
            conn.close()

    # ... [继续下一部分] ...