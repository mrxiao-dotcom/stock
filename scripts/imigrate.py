import sqlite3
import mysql.connector
import logging
from datetime import datetime
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

# MySQL配置
MYSQL_CONFIG = {
    'host': '10.17.31.104',
    'user': 'root',
    'password': 'Xj774913@',
    'port': 3306,
    'database': 'stock',
    'charset': 'utf8mb4'
}

# SQLite配置
SQLITE_DB_PATH = 'example.db'  # 替换为你的实际 SQLite 数据库文件路径


def get_sqlite_tables(sqlite_conn):
    """获取SQLite数据库中的所有表"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [table[0] for table in cursor.fetchall()]


def get_table_schema(sqlite_conn, table_name):
    """获取表结构"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def create_mysql_table(mysql_conn, table_name, schema):
    """在MySQL中创建表"""
    # SQLite到MySQL的类型映射
    type_mapping = {
        'INTEGER': 'INT',
        'REAL': 'DOUBLE',
        'TEXT': 'VARCHAR(255)',
        'BLOB': 'BLOB',
        'VARCHAR': 'VARCHAR(255)',
        'DATETIME': 'DATETIME',
        'BOOLEAN': 'TINYINT(1)',
        'DECIMAL': 'DECIMAL(20,4)',
        'TIMESTAMP': 'TIMESTAMP'
    }

    cursor = mysql_conn.cursor()

    # 构建建表SQL
    columns = []
    primary_keys = []

    for col in schema:
        name = col[1]
        col_type = col[2].upper()
        is_pk = col[5]

        # 主键字段必须设置为 NOT NULL
        not_null = "NOT NULL" if (col[3] or is_pk) else "NULL"

        # 特殊处理 update_time 字段
        if name == 'update_time':
            column_def = "`update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        # 特殊处理 trade_date 字段
        elif name == 'trade_date':
            column_def = f"`{name}` VARCHAR(20) {not_null}"
        else:
            # 映射类型
            mysql_type = type_mapping.get(col_type, 'VARCHAR(255)')

            # 处理默认值
            default = ""
            if col[4] is not None:
                if col[4] == "CURRENT_TIMESTAMP":
                    default = "DEFAULT CURRENT_TIMESTAMP"
                elif mysql_type in ['INT', 'DOUBLE', 'DECIMAL']:
                    default = f"DEFAULT {col[4]}"
                elif col[4].upper() == 'NULL' and not is_pk:
                    default = "DEFAULT NULL"
                else:
                    default = f"DEFAULT '{col[4]}'"
            elif is_pk and mysql_type in ['INT', 'BIGINT']:
                default = "DEFAULT 0"
            elif is_pk and mysql_type.startswith('VARCHAR'):
                default = "DEFAULT ''"

            column_def = f"`{name}` {mysql_type} {not_null} {default}".strip()

        columns.append(column_def)

        if is_pk:
            primary_keys.append(f"`{name}`")

    # 添加主键定义
    if primary_keys:
        columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        {', '.join(columns)}
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    try:
        # 先尝试删除已存在的表
        drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
        cursor.execute(drop_sql)
        mysql_conn.commit()

        # 创建新表
        cursor.execute(create_sql)
        mysql_conn.commit()
        logging.info(f"表 {table_name} 创建成功")
        logging.debug(f"建表SQL: {create_sql}")
    except Exception as e:
        logging.error(f"创建表 {table_name} 失败: {str(e)}")
        logging.debug(f"失败的SQL: {create_sql}")
        raise


def migrate_data(sqlite_conn, mysql_conn, table_name):
    """迁移数据"""
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()

    try:
        # 获取数据
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            logging.info(f"表 {table_name} 没有数据需要迁移")
            return

        # 获取列名
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]

        # 构建插入SQL
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"""
        INSERT INTO `{table_name}` 
        (`{'`, `'.join(columns)}`) 
        VALUES ({placeholders})
        """

        # 批量插入数据
        batch_size = 1000
        total_rows = len(rows)
        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]
            mysql_cursor.executemany(insert_sql, batch)
            mysql_conn.commit()
            logging.info(f"表 {table_name} 已迁移 {min(i + batch_size, total_rows)}/{total_rows} 条记录")

        logging.info(f"表 {table_name} 数据迁移完成")

    except Exception as e:
        logging.error(f"迁移表 {table_name} 数据失败: {str(e)}")
        raise


def print_database_info(sqlite_conn):
    """打印数据库中所有表的信息"""
    cursor = sqlite_conn.cursor()
    tables = get_sqlite_tables(sqlite_conn)
    
    logging.info("SQLite 数据库中的表信息：")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logging.info(f"表名: {table}, 记录数: {count}")
    return tables


def main():
    start_time = datetime.now()
    logging.info("开始数据库迁移...")

    try:
        # 修改连接数据库的部分
        logging.info(f"正在连接 SQLite 数据库: {SQLITE_DB_PATH}")
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # 打印数据库信息
        print_database_info(sqlite_conn)
        
        logging.info("正在连接 MySQL 数据库...")
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        logging.info("数据库连接成功")

        # 获取所有表
        tables = get_sqlite_tables(sqlite_conn)
        logging.info(f"找到 {len(tables)} 个表需要迁移")

        # 迁移每个表
        for table in tables:
            try:
                logging.info(f"\n开始迁移表 {table}")

                # 获取表结构
                schema = get_table_schema(sqlite_conn, table)

                # 创建MySQL表
                create_mysql_table(mysql_conn, table, schema)

                # 迁移数据
                migrate_data(sqlite_conn, mysql_conn, table)

            except Exception as e:
                logging.error(f"迁移表 {table} 失败: {str(e)}\n{traceback.format_exc()}")
                continue

        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"\n数据库迁移完成！耗时: {duration}")

    except Exception as e:
        logging.error(f"数据库迁移失败: {str(e)}\n{traceback.format_exc()}")

    finally:
        # 关闭连接
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'mysql_conn' in locals():
            mysql_conn.close()


if __name__ == "__main__":
    main()