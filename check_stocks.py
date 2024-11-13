import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_stocks(stock_names):
    """检查指定股票是否在数据库中"""
    try:
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        
        logger.info("检查数据库中的股票信息:")
        
        # 首先显示总体统计
        cursor.execute('SELECT COUNT(*) FROM stocks')
        total_count = cursor.fetchone()[0]
        logger.info(f"数据库中共有 {total_count} 只股票")
        
        # 检查指定的股票
        for stock_name in stock_names:
            cursor.execute('SELECT "证券代码", "证券简称" FROM stocks WHERE "证券简称" = ?', (stock_name,))
            result = cursor.fetchone()
            if result:
                logger.info(f"找到股票: {result[1]} ({result[0]})")
            else:
                logger.warning(f"未找到股票: {stock_name}")
        
        # 显示部分示例数据
        logger.info("\n数据库中的部分股票示例:")
        cursor.execute('SELECT "证券代码", "证券简称" FROM stocks LIMIT 5')
        for row in cursor.fetchall():
            logger.info(f"- {row[1]} ({row[0]})")
            
    except Exception as e:
        logger.error(f"检查数据库失败: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 要检查的股票名称
    stocks_to_check = ['高新发展', '华神科技', '美利云', '登云股份', '金证股份', '博通股份']
    check_stocks(stocks_to_check) 