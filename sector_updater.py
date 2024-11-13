import baostock as bs
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SectorUpdater:
    def __init__(self, db_path='example.db'):
        self.db_path = db_path
        
    def get_sector_id(self, sector_code):
        """获取板块ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT sector_id FROM sectors WHERE sector_code = ?', (sector_code,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
        
    @staticmethod
    def convert_baostock_code(baostock_code):
        """转换 BaoStock 代码为本地数据库格式
        例如: sh.600000 -> 600000.SH, sz.000001 -> 000001.SZ
        """
        if not baostock_code:
            return None
        try:
            market, code = baostock_code.split('.')
            if market.upper() == 'SH':
                return f"{code}.SH"
            elif market.upper() == 'SZ':
                return f"{code}.SZ"
            return None
        except:
            return None
        
    def update_existing_stock_codes(self):
        """更新现有数据中的股票代码格式"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有需要更新的股票代码
            cursor.execute('SELECT stock_code FROM sector_stocks')
            stock_codes = cursor.fetchall()
            
            for (old_code,) in stock_codes:
                if '.' in old_code:
                    parts = old_code.split('.')
                    if len(parts) == 2:
                        code, market = parts
                        # 确保市场代码是大写的
                        new_code = f"{code}.{market.upper()}"
                        if new_code != old_code:
                            cursor.execute('''
                                UPDATE sector_stocks 
                                SET stock_code = ? 
                                WHERE stock_code = ?
                            ''', (new_code, old_code))
                            logger.info(f"更新股票代码: {old_code} -> {new_code}")
            
            conn.commit()
            logger.info("完成股票代码格式更新")
            
        except Exception as e:
            logger.error(f"更新股票代码格式失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

    def update_sector_stocks(self, sector_code):
        """更新指定板块的成分股"""
        try:
            # 登录系统
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"登录失败: {lg.error_msg}")
                return {
                    'success': False,
                    'message': f"登录失败: {lg.error_msg}"
                }
                
            try:
                # 获取板块ID
                sector_id = self.get_sector_id(sector_code)
                if not sector_id:
                    logger.error(f"未找到板块: {sector_code}")
                    return {
                        'success': False,
                        'message': f"未找到板块: {sector_code}"
                    }
                
                # 根据板块代码调用相应的接口
                if sector_code == 'SZ50':
                    rs = bs.query_sz50_stocks()
                elif sector_code == 'HS300':
                    rs = bs.query_hs300_stocks()
                elif sector_code == 'ZZ500':
                    rs = bs.query_zz500_stocks()
                else:
                    logger.error(f"不支持的板块代码: {sector_code}")
                    return {
                        'success': False,
                        'message': f"不支持的板块代码: {sector_code}"
                    }
                
                if rs.error_code != '0':
                    logger.error(f"获取成分股失败: {rs.error_msg}")
                    return {
                        'success': False,
                        'message': f"获取成分股失败: {rs.error_msg}"
                    }
                
                # 获取成分股数据
                stocks = []
                while (rs.error_code == '0') & rs.next():
                    baostock_code = rs.get_row_data()[1]  # 获取股票代码
                    db_code = self.convert_baostock_code(baostock_code)
                    if db_code:
                        stocks.append(db_code)
                        logger.debug(f"转换股票代码: {baostock_code} -> {db_code}")
                
                if not stocks:
                    logger.warning(f"未获取到成分股数据: {sector_code}")
                    return {
                        'success': False,
                        'message': f"未获取到成分股数据: {sector_code}"
                    }
                
                # 更新数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                try:
                    # 获取当前成分股
                    cursor.execute('SELECT stock_code FROM sector_stocks WHERE sector_id = ?', (sector_id,))
                    current_stocks = set(row[0] for row in cursor.fetchall())
                    
                    # 新的成分股集合
                    new_stocks = set(stocks)
                    
                    # 计算需要添加和删除的股票
                    stocks_to_add = new_stocks - current_stocks
                    stocks_to_remove = current_stocks - new_stocks
                    unchanged_stocks = current_stocks & new_stocks
                    
                    # 删除不再是成分股的股票
                    if stocks_to_remove:
                        placeholders = ','.join('?' * len(stocks_to_remove))
                        cursor.execute(f'''
                            DELETE FROM sector_stocks 
                            WHERE sector_id = ? AND stock_code IN ({placeholders})
                        ''', (sector_id,) + tuple(stocks_to_remove))
                        logger.info(f"删除 {len(stocks_to_remove)} 只股票")
                    
                    # 添加新的成分股
                    update_time = datetime.now()
                    for stock_code in stocks_to_add:
                        cursor.execute('''
                            INSERT INTO sector_stocks (sector_id, stock_code, update_time)
                            VALUES (?, ?, ?)
                        ''', (sector_id, stock_code, update_time))
                        logger.info(f"添加新股票: {stock_code}")
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'message': f"更新成功",
                        'stats': {
                            'added': len(stocks_to_add),
                            'removed': len(stocks_to_remove),
                            'unchanged': len(unchanged_stocks),
                            'total': len(new_stocks)
                        }
                    }
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"更新数据库失败: {str(e)}")
                    return {
                        'success': False,
                        'message': f"更新数据库失败: {str(e)}"
                    }
                finally:
                    conn.close()
                    
            finally:
                bs.logout()
                
        except Exception as e:
            logger.error(f"更新成分股时出错: {str(e)}")
            return {
                'success': False,
                'message': f"更新成分股时出错: {str(e)}"
            }
            
    def update_all_sectors(self):
        """更新所有指数板块的成分股"""
        # 首先更新现有数据中的股票代码格式
        self.update_existing_stock_codes()
        
        sectors = ['SZ50', 'HS300', 'ZZ500']
        results = {}
        
        for sector_code in sectors:
            logger.info(f"开始更新 {sector_code} 成分股...")
            result = self.update_sector_stocks(sector_code)
            results[sector_code] = result
            
            if result['success']:
                logger.info(f"{sector_code} 更新成功: {result['stats']}")
            else:
                logger.error(f"{sector_code} 更新失败: {result['message']}")
        
        return results

    def save_custom_sector(self, sector_name, stock_list):
        """保存自定义板块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 检查板块是否已存在
                cursor.execute('SELECT sector_id FROM sectors WHERE sector_name = ?', (sector_name,))
                result = cursor.fetchone()
                
                if result:
                    sector_id = result[0]
                    # 更新现有板块
                    cursor.execute('''
                        UPDATE sectors 
                        SET update_time = datetime('now')
                        WHERE sector_id = ?
                    ''', (sector_id,))
                else:
                    # 创建新板块
                    cursor.execute('''
                        INSERT INTO sectors (sector_name, sector_type, update_time)
                        VALUES (?, 'CUSTOM', datetime('now'))
                    ''', (sector_name,))
                    sector_id = cursor.lastrowid
                
                # 清除旧的关联关系
                cursor.execute('DELETE FROM sector_stocks WHERE sector_id = ?', (sector_id,))
                
                # 添加新的关联关系
                for stock in stock_list:
                    cursor.execute('''
                        INSERT INTO sector_stocks (sector_id, stock_code, update_time)
                        VALUES (?, ?, datetime('now'))
                    ''', (sector_id, stock))
                
                conn.commit()
                return {
                    'success': True,
                    'message': '保存成功',
                    'sector_id': sector_id
                }
                
            except Exception as e:
                conn.rollback()
                logger.error(f"保存板块失败: {str(e)}")
                return {
                    'success': False,
                    'message': str(e)
                }
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def rename_sector(self, sector_id, new_name):
        """重命名板块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 检查新名称是否已存在
                cursor.execute('SELECT sector_id FROM sectors WHERE sector_name = ? AND sector_id != ?', 
                             (new_name, sector_id))
                if cursor.fetchone():
                    return {
                        'success': False,
                        'message': '板块名称已存在'
                    }
                
                cursor.execute('''
                    UPDATE sectors 
                    SET sector_name = ?, update_time = datetime('now')
                    WHERE sector_id = ?
                ''', (new_name, sector_id))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'message': '未找到指定板块'
                    }
                
                conn.commit()
                return {
                    'success': True,
                    'message': '重命名成功'
                }
                
            except Exception as e:
                conn.rollback()
                logger.error(f"重命名板块失败: {str(e)}")
                return {
                    'success': False,
                    'message': str(e)
                }
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def delete_sector(self, sector_id):
        """删除板块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 检查是否是系统板块
                cursor.execute('SELECT sector_type FROM sectors WHERE sector_id = ?', (sector_id,))
                result = cursor.fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'message': '未找到指定板块'
                    }
                
                if result[0] == 'INDEX':
                    return {
                        'success': False,
                        'message': '系统板块不能删除'
                    }
                
                # 删除板块关联关系
                cursor.execute('DELETE FROM sector_stocks WHERE sector_id = ?', (sector_id,))
                
                # 删除板块
                cursor.execute('DELETE FROM sectors WHERE sector_id = ?', (sector_id,))
                
                conn.commit()
                return {
                    'success': True,
                    'message': '删除成功'
                }
                
            except Exception as e:
                conn.rollback()
                logger.error(f"删除板块失败: {str(e)}")
                return {
                    'success': False,
                    'message': str(e)
                }
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }

if __name__ == "__main__":
    updater = SectorUpdater()
    results = updater.update_all_sectors()
    print("更新结果:", results)