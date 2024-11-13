import baostock as bs
import pandas as pd
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_stock_list():
    """更新股票基础信息"""
    try:
        # 登录系统
        lg = bs.login()
        if lg.error_code != '0':
            logger.error(f"登录失败: {lg.error_msg}")
            return False
            
        try:
            # 获取证券基本资料
            rs = bs.query_stock_basic()
            if rs.error_code != '0':
                logger.error(f"获取股票列表失败: {rs.error_msg}")
                return False
            
            # 处理数据
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                stock_list.append(rs.get_row_data())
            
            if not stock_list:
                logger.error("未获取到股票数据")
                return False
            
            # 转换为DataFrame
            df = pd.DataFrame(stock_list, columns=rs.fields)
            
            # 连接数据库
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            
            try:
                # 删除旧数据
                cursor.execute('DROP TABLE IF EXISTS stocks')
                
                # 创建新表
                cursor.execute('''
                    CREATE TABLE stocks (
                        "证券代码" TEXT PRIMARY KEY,
                        "证券简称" TEXT,
                        "证券类型" TEXT,
                        "上市状态" TEXT,
                        "上市日期" TEXT,
                        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 插入数据
                for _, row in df.iterrows():
                    cursor.execute('''
                        INSERT INTO stocks ("证券代码", "证券简称", "证券类型", "上市状态", "上市日期")
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row['code'],
                        row['code_name'],
                        row['type'],
                        row['status'],
                        row['ipoDate']
                    ))
                
                conn.commit()
                logger.info(f"成功更新股票列表，共 {len(df)} 只股票")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"更新数据库失败: {str(e)}")
                return False
            finally:
                conn.close()
                
        finally:
            bs.logout()
            
    except Exception as e:
        logger.error(f"更新股票列表失败: {str(e)}")
        return False

if __name__ == "__main__":
    update_stock_list() 