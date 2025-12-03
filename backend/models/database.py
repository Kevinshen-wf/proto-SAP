import psycopg2
from psycopg2 import sql
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.config import get_db_config
import hashlib

# 导入操作日志记录器
from backend.operation_logger import operation_logger

# 创建全局数据库管理器实例
db_manager = None

def get_db_manager():
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

class DatabaseManager:
    def __init__(self):
        self.db_config = get_db_config()
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = psycopg2.connect(**self.db_config)
            return connection
        except psycopg2.OperationalError as error:
            print(f"数据库连接操作错误: {error}")
            return None
        except psycopg2.DatabaseError as error:
            print(f"数据库错误: {error}")
            return None
        except Exception as error:
            print(f"数据库连接失败: {error}")
            return None
    
    def query_table(self, table_name, search_column=None, search_value=None, sort_column=None, sort_order='asc'):
        """查询指定表的数据"""
        conn = self.get_connection()
        if not conn:
            print("无法获取数据库连接")
            return []
        
        try:
            cursor = conn.cursor()
            
            # 首先检查表是否存在
            check_table_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s
            """
            cursor.execute(check_table_query, (table_name,))
            if not cursor.fetchone():
                print(f"表 {table_name} 不存在")
                cursor.close()
                conn.close()
                return []
            
            # 对于wf_open表，添加chinese_name和unit列（如果不存在）
            if table_name == 'wf_open':
                # 检查列是否存在，如果不存在则添加
                check_column_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'purchase_orders' 
                    AND table_name = %s 
                    AND column_name IN ('chinese_name', 'unit')
                """
                cursor.execute(check_column_query, (table_name,))
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # 如果列不存在，则添加它们
                if 'chinese_name' not in existing_columns:
                    add_chinese_name_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN chinese_name VARCHAR(100)"
                    cursor.execute(add_chinese_name_query)
                
                if 'unit' not in existing_columns:
                    add_unit_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN unit VARCHAR(20)"
                    cursor.execute(add_unit_query)
            
            # 对于 closed 表，添加 id 列和 shipment_batch_no 列（如果不存在）
            if table_name in ['wf_closed', 'non_wf_closed']:
                # 检查 id 列是否存在
                check_id_query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'purchase_orders' 
                    AND table_name = %s 
                    AND column_name IN ('id', 'shipment_batch_no')
                """
                cursor.execute(check_id_query, (table_name,))
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # 添加 id 列（如果不存在）
                if 'id' not in existing_columns:
                    add_id_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN id SERIAL PRIMARY KEY"
                    try:
                        cursor.execute(add_id_query)
                    except:
                        # 如果带 PRIMARY KEY 失败，仅添加不带 PK 的 id 列
                        add_id_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN id SERIAL"
                        cursor.execute(add_id_query)
                
                # 添加 shipment_batch_no 列（如果不存在）
                if 'shipment_batch_no' not in existing_columns:
                    add_batch_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN shipment_batch_no VARCHAR(50)"
                    cursor.execute(add_batch_query)
            
            # 构建查询语句
            if search_column and search_value:
                # 构建带搜索条件的查询
                query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE {}::text ILIKE %s").format(
                    sql.Identifier(table_name),
                    sql.Identifier(search_column)
                )
                cursor.execute(query, (f"%{search_value}%",))
            elif sort_column:
                # 构建带排序的查询
                query = sql.SQL("SELECT * FROM purchase_orders.{} ORDER BY {} {}").format(
                    sql.Identifier(table_name),
                    sql.Identifier(sort_column),
                    sql.SQL(sort_order.upper())
                )
                cursor.execute(query)
            else:
                # 默认查询
                query = sql.SQL("SELECT * FROM purchase_orders.{}").format(
                    sql.Identifier(table_name)
                )
                cursor.execute(query)
            
            records = cursor.fetchall()
            
            # 获取列名
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()
            
            # 转换为字典列表
            result = []
            for record in records:
                row_dict = {}
                for i, colname in enumerate(colnames):
                    row_dict[colname] = record[i]
                result.append(row_dict)
            
            return result
        except Exception as error:
            print(f"查询表 {table_name} 时出错: {error}")
            if conn:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass
            return []
    
    def get_all_tables(self):
        """获取所有表名"""
        conn = self.get_connection()
        if not conn:
            print("无法获取数据库连接")
            return []
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'purchase_orders'
                ORDER BY table_name
            """
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return tables
        except Exception as error:
            print(f"获取表名时出错: {error}")
            if conn:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass
            return []
    
    def generate_row_hash(self, row_data):
        """为行数据生成哈希值用于版本控制"""
        # 将行数据转换为字符串并生成哈希
        row_str = str(sorted(row_data.items()))
        return hashlib.md5(row_str.encode()).hexdigest()
    
    def update_row(self, table_name, pn, updates, user_email=None):
        """
        更新表中的数据
        
        Args:
            table_name: 表名
            pn: 主键值
            updates: 要更新的字段字典 {column_name: new_value}
            user_email: 用户邮箱（用于记录操作日志）
            
        Returns:
            tuple: (success, message)
        """
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"
        
        try:
            cursor = conn.cursor()
            
            # 确定主键字段
            primary_key_field = 'id'  # 默认使用新的自增主键
            primary_key_value = pn
            
            # 对于wf_open和non_wf_open表，我们需要根据pn查找对应的po_line
            if table_name in ['wf_open', 'non_wf_open']:
                # 先根据pn查找po_line
                find_po_line_query = f"SELECT po_line FROM purchase_orders.{table_name} WHERE pn = %s LIMIT 1"
                cursor.execute(find_po_line_query, (pn,))
                result = cursor.fetchone()
                if result:
                    primary_key_field = 'po_line'
                    primary_key_value = result[0]  # 使用找到的po_line作为主键
                else:
                    # 如果找不到对应的po_line，则直接使用pn进行查找
                    primary_key_field = 'pn'
            elif table_name in ['wf_closed', 'non_wf_closed']:
                # 对于closed表：如果传进来的是整数，可能是id
                try:
                    id_value = int(pn)
                    primary_key_field = 'id'
                    primary_key_value = id_value
                except (ValueError, TypeError):
                    # 不是整数，使用pn作为主键
                    primary_key_field = 'pn'
                    primary_key_value = pn
            
            # 构建更新查询
            set_clauses = []
            values = []
            for column_name, new_value in updates.items():
                set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(column_name)))
                # 处理日期字段的特殊格式
                if column_name in ['req_date_wf', 'eta_wfsz', 'latest_departure_date', 'po_placed_date']:
                    if new_value is None or new_value == '' or new_value == 'None' or new_value == 'nan':
                        values.append(None)
                    else:
                        values.append(new_value)
                else:
                    # 处理其他字段的空值
                    if new_value == 'None' or new_value == 'nan':
                        values.append(None)
                    else:
                        values.append(new_value)
            
            # 添加主键值
            values.append(primary_key_value)
            
            update_query = sql.SQL("UPDATE purchase_orders.{} SET {} WHERE {} = %s").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(set_clauses),
                sql.Identifier(primary_key_field)
            )
            
            cursor.execute(update_query, values)
            affected_rows = cursor.rowcount
            conn.commit()
            
            # 记录操作日志
            if user_email and affected_rows > 0:
                # 获取更新前的记录数据用于日志记录
                try:
                    select_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE {} = %s").format(
                        sql.Identifier(table_name),
                        sql.Identifier(primary_key_field)
                    )
                    cursor.execute(select_query, (primary_key_value,))
                    updated_record = cursor.fetchone()
                    
                    # 获取列名
                    colnames = [desc[0] for desc in cursor.description]
                    
                    # 转换为字典
                    if updated_record:
                        record_data = dict(zip(colnames, updated_record))
                        # 记录操作日志
                        operation_logger.log_operation(
                            user_email=user_email,
                            table_name=table_name,
                            operation='update',
                            record_data=record_data
                        )
                except Exception as log_error:
                    print(f"记录更新操作日志时出错: {log_error}")
            
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                return True, f"更新成功，影响了 {affected_rows} 行"
            else:
                return False, "未找到要更新的记录或数据未发生变化"
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return False, f"更新数据时出错: {error}"
    
    def delete_row(self, table_name, key, user_email=None, key_field='pn'):
        """
        删除表中的数据
        
        Args:
            table_name: 表名
            key: 主键值
            user_email: 用户邮箱（用于记录操作日志）
            key_field: 主键字段名，默认为 'pn'
            
        Returns:
            tuple: (success, message)
        """
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"
        
        try:
            cursor = conn.cursor()
            
            # 获取删除前的记录数据用于日志记录
            deleted_record = None
            if user_email:
                try:
                    select_query = sql.SQL("SELECT * FROM purchase_orders.{} WHERE {} = %s").format(
                        sql.Identifier(table_name),
                        sql.Identifier(key_field)
                    )
                    cursor.execute(select_query, (key,))
                    deleted_record_row = cursor.fetchone()
                    
                    # 获取列名
                    if deleted_record_row:
                        colnames = [desc[0] for desc in cursor.description]
                        deleted_record = dict(zip(colnames, deleted_record_row))
                except Exception as log_error:
                    print(f"获取删除前记录数据时出错: {log_error}")
            
            # 执行删除
            delete_query = sql.SQL("DELETE FROM purchase_orders.{} WHERE {} = %s").format(
                sql.Identifier(table_name),
                sql.Identifier(key_field)
            )
            cursor.execute(delete_query, (key,))
            affected_rows = cursor.rowcount
            conn.commit()
            
            # 记录操作日志
            if user_email and affected_rows > 0 and deleted_record:
                try:
                    # 记录操作日志
                    operation_logger.log_operation(
                        user_email=user_email,
                        table_name=table_name,
                        operation='delete',
                        record_data=deleted_record
                    )
                except Exception as log_error:
                    print(f"记录删除操作日志时出错: {log_error}")
            
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                return True, f"删除成功，影响了 {affected_rows} 行"
            else:
                return False, "未找到要删除的记录"
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return False, f"删除数据时出错: {error}"
    
    def insert_row(self, table_name, data, user_email=None):
        """
        插入新行数据
        
        Args:
            table_name: 表名
            data: 要插入的数据字典 {column_name: value}
            user_email: 用户邮箱（用于记录操作日志）
            
        Returns:
            tuple: (success, message)
        """
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"
        
        try:
            cursor = conn.cursor()
            
            # 获取表的实际列名
            get_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s
            """
            cursor.execute(get_columns_query, (table_name,))
            existing_columns = set(row[0] for row in cursor.fetchall())
            
            # 清理数据中的特殊值，只保留表中存在的列
            cleaned_data = {}
            for k, v in data.items():
                if k not in existing_columns:
                    # 跳过不存在的列
                    print(f"跳过不存在的列: {k}")
                    continue
                if v == 'None' or v == 'nan' or v == '':
                    cleaned_data[k] = None
                else:
                    cleaned_data[k] = v
            
            # 根据表名确定主键字段和处理策略
            if table_name in ['wf_open', 'non_wf_open']:
                # WF Open和Non-WF Open表使用po_line作为主键，使用ON CONFLICT处理
                columns = list(cleaned_data.keys())
                values = list(cleaned_data.values())
                
                # 构建ON CONFLICT更新的SET子句
                update_fields = []
                for col in columns:
                    if col != 'po_line':  # 主键字段不更新
                        update_fields.append(f"{col} = EXCLUDED.{col}")
                
                insert_query = sql.SQL("""
                    INSERT INTO purchase_orders.{} ({}) 
                    VALUES ({}) 
                    ON CONFLICT (po_line) DO UPDATE SET {}
                """).format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                    sql.SQL(", ").join(sql.Placeholder() * len(columns)),
                    sql.SQL(", ".join(update_fields) if update_fields else "po = EXCLUDED.po")
                )
            else:
                # 其他表使用默认的插入方式
                columns = list(cleaned_data.keys())
                values = list(cleaned_data.values())
                placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
                
                insert_query = sql.SQL("INSERT INTO purchase_orders.{} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(sql.Identifier(col) for col in columns),
                    placeholders
                )
            
            cursor.execute(insert_query, values)
            affected_rows = cursor.rowcount
            conn.commit()
            
            # 记录操作日志
            if user_email and affected_rows > 0:
                # 记录操作日志
                operation_logger.log_operation(
                    user_email=user_email,
                    table_name=table_name,
                    operation='insert',
                    record_data=cleaned_data
                )
            
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                return True, f"插入成功，影响了 {affected_rows} 行"
            else:
                return False, "插入失败"
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return False, f"插入数据时出错: {error}"
    
    def add_dynamic_columns(self, table_name, column_definitions):
        """
        为表动态添加列
        
        Args:
            table_name: 表名
            column_definitions: 列定义字典 {column_name: data_type}
        """
        conn = self.get_connection()
        if not conn:
            return False, "数据库连接失败"
        
        try:
            cursor = conn.cursor()
            
            # 检查列是否已存在
            check_column_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s 
                AND column_name = %s
            """
            
            for column_name, data_type in column_definitions.items():
                cursor.execute(check_column_query, (table_name, column_name))
                if not cursor.fetchone():
                    # 列不存在，添加它
                    add_column_query = sql.SQL("ALTER TABLE purchase_orders.{} ADD COLUMN {} {}").format(
                        sql.Identifier(table_name),
                        sql.Identifier(column_name),
                        sql.SQL(data_type)
                    )
                    cursor.execute(add_column_query)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, "列添加成功"
        except Exception as error:
            if conn:
                try:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                except:
                    pass
            return False, f"添加列时出错: {error}"

    def check_duplicates(self, table_name, data_list):
        """
        检查数据列表中是否存在主键冲突
        
        Args:
            table_name: 表名
            data_list: 要检查的数据列表
            
        Returns:
            list: 重复的数据项列表
        """
        conn = self.get_connection()
        if not conn:
            raise Exception("数据库连接失败")
        
        try:
            cursor = conn.cursor()
            duplicates = []
            
            # 根据表名确定主键字段
            primary_key_field = 'id'  # 默认使用新的自增主键
            if table_name in ['wf_open', 'non_wf_open']:
                primary_key_field = 'po_line'
            elif table_name in ['wf_closed', 'non_wf_closed']:
                # 对于新表结构，我们通过pn字段检查重复
                primary_key_field = 'pn'
            
            # 检查每个数据项
            for data in data_list:
                # 获取主键值
                primary_key_value = data.get(primary_key_field)
                if not primary_key_value:
                    continue
                
                # 查询数据库中是否存在相同的主键
                query = sql.SQL("SELECT COUNT(*) FROM purchase_orders.{} WHERE {} = %s").format(
                    sql.Identifier(table_name),
                    sql.Identifier(primary_key_field)
                )
                cursor.execute(query, (primary_key_value,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # 如果存在，添加到重复列表中
                    duplicates.append({
                        'data': data,
                        'primary_key': primary_key_value
                    })
            
            return duplicates
        except Exception as error:
            if conn:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass
            raise error

# 全局函数，供外部调用
def get_table_data(table_name, search_column=None, search_value=None, sort_column=None, sort_order='asc'):
    """获取表数据"""
    try:
        manager = get_db_manager()
        return manager.query_table(table_name, search_column, search_value, sort_column, sort_order)
    except Exception as e:
        print(f"获取表数据时出错: {e}")
        return []

def get_all_tables():
    """获取所有表名"""
    try:
        manager = get_db_manager()
        return manager.get_all_tables()
    except Exception as e:
        print(f"获取所有表名时出错: {e}")
        return []

def update_table_data(table_name, row_data, primary_key_value):
    """更新表数据"""
    try:
        manager = get_db_manager()
        return manager.update_row(table_name, primary_key_value, row_data)
    except Exception as e:
        print(f"更新表数据时出错: {e}")
        return False, f"更新数据时出错: {e}"

def insert_table_data(table_name, row_data, user_email=None):
    """插入表数据"""
    try:
        manager = get_db_manager()
        return manager.insert_row(table_name, row_data, user_email)
    except Exception as e:
        print(f"插入表数据时出错: {e}")
        return False, f"插入数据时出错: {e}"

def delete_table_data(table_name, primary_key_value):
    """删除表数据"""
    try:
        manager = get_db_manager()
        return manager.delete_row(table_name, primary_key_value)
    except Exception as e:
        print(f"删除表数据时出错: {e}")
        return False, f"删除数据时出错: {e}"

def add_dynamic_columns(table_name, column_definitions):
    """动态添加列"""
    try:
        manager = get_db_manager()
        return manager.add_dynamic_columns(table_name, column_definitions)
    except Exception as e:
        print(f"动态添加列时出错: {e}")
        return False, f"添加列时出错: {e}"