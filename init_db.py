#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建采购订单管理系统所需的数据库表
"""

import psycopg2
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_config():
    """从环境变量获取数据库配置"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'purchase_orders'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }

def create_purchase_orders_schema(cursor):
    """创建purchase_orders模式"""
    try:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS purchase_orders")
        print("✓ 成功创建purchase_orders模式")
    except Exception as e:
        print(f"✗ 创建purchase_orders模式时出错: {e}")

def create_wf_open_table(cursor):
    """创建WF Open表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.wf_open (
            po VARCHAR(50),
            pn VARCHAR(50) NULL,
            line INTEGER,
            po_line VARCHAR(50) PRIMARY KEY,
            description TEXT,
            qty DECIMAL(10, 2),
            net_price DECIMAL(10, 4),
            total_price DECIMAL(10, 2),
            req_date_wf DATE,
            po_placed_date DATE,
            purchaser VARCHAR(100),
            wfnl_eta DATE,
            wfsz_shipping_mode VARCHAR(100),
            comment TEXT,
            record_no VARCHAR(50),
            shipping_cost DECIMAL(10, 2),
            tracking_no VARCHAR(100),
            so_number VARCHAR(50),
            latest_departure_date DATE,
            chinese_name VARCHAR(100),
            unit VARCHAR(20),
            eta_wfsz DATE,
            company VARCHAR(100)
        )
        """
        cursor.execute(create_table_query)
        print("✓ 成功创建WF Open表")
    except Exception as e:
        print(f"✗ 创建WF Open表时出错: {e}")

def create_wf_closed_table(cursor):
    """创建 WF Closed表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.wf_closed (
            id SERIAL PRIMARY KEY,
            po VARCHAR(50),
            pn VARCHAR(50) NULL,
            line INTEGER,
            po_line VARCHAR(50),
            description TEXT,
            qty DECIMAL(10, 2),
            net_price DECIMAL(10, 4),
            total_price DECIMAL(10, 2),
            req_date_wf DATE,
            po_placed_date DATE,
            purchaser VARCHAR(100),
            wfnl_eta DATE,
            wfsz_shipping_mode VARCHAR(100),
            comment TEXT,
            record_no VARCHAR(50),
            shipping_cost DECIMAL(10, 2),
            tracking_no VARCHAR(100),
            so_number VARCHAR(50),
            latest_departure_date DATE,
            chinese_name VARCHAR(100),
            unit VARCHAR(20),
            eta_wfsz DATE,
            company VARCHAR(100),
            shipment_batch_no VARCHAR(50)
        )
        """
        cursor.execute(create_table_query)
        print("✓ 成功创建 WF Closed表")
    except Exception as e:
        print(f"✗ 创建 WF Closed表時出错: {e}")

def create_non_wf_open_table(cursor):
    """创建Non-WF Open表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.non_wf_open (
            po VARCHAR(50),
            pn VARCHAR(50) NULL,
            description TEXT,
            qty DECIMAL(10, 2),
            net_price DECIMAL(10, 4),
            total_price DECIMAL(10, 2),
            req_date DATE,
            po_placed_date DATE,
            eta DATE,
            eta_wfsz DATE,
            shipping_mode VARCHAR(100),
            comment TEXT,
            record_no VARCHAR(50),
            shipping_cost DECIMAL(10, 2),
            tracking_no VARCHAR(100),
            so_number VARCHAR(50),
            latest_departure_date DATE,
            qc_result VARCHAR(50),
            yes_not_paid VARCHAR(10),
            line VARCHAR(50),
            po_line VARCHAR(100) PRIMARY KEY,
            company VARCHAR(100)
        )
        """
        cursor.execute(create_table_query)
        print("✓ 成功创建Non-WF Open表")
    except Exception as e:
        print(f"✗ 创建Non-WF Open表时出错: {e}")

def create_non_wf_closed_table(cursor):
    """创建 Non-WF Closed表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.non_wf_closed (
            id SERIAL PRIMARY KEY,
            po VARCHAR(50),
            pn VARCHAR(50) NULL,
            description TEXT,
            qty DECIMAL(10, 2),
            net_price DECIMAL(10, 4),
            total_price DECIMAL(10, 2),
            req_date DATE,
            po_placed_date DATE,
            eta DATE,
            eta_wfsz DATE,
            shipping_mode VARCHAR(100),
            comment TEXT,
            record_no VARCHAR(50),
            shipping_cost DECIMAL(10, 2),
            tracking_no VARCHAR(100),
            so_number VARCHAR(50),
            latest_departure_date DATE,
            purchaser VARCHAR(100),
            yes_not_paid VARCHAR(10),
            line VARCHAR(50),
            po_line VARCHAR(100),
            company VARCHAR(100),
            shipment_batch_no VARCHAR(50)
        )
        """
        cursor.execute(create_table_query)
        print("✓ 成功创建 Non-WF Closed表")
    except Exception as e:
        print(f"✗ 创建 Non-WF Closed表時出错: {e}")

def add_shipment_batch_no_column(cursor):
    """
    为closed表添加shipment_batch_no列和id列
    """
    try:
        tables = ['wf_closed', 'non_wf_closed']
        for table_name in tables:
            # 检查列是否已经存在
            check_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s 
                AND column_name IN ('shipment_batch_no', 'id')
            """
            cursor.execute(check_columns_query, (table_name,))
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # 添加id列（如果不存在）
            if 'id' not in existing_columns:
                try:
                    add_id_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN id SERIAL PRIMARY KEY"
                    cursor.execute(add_id_query)
                    print(f"✓ 成功添加id列到{table_name}表")
                except:
                    # 如果带PRIMARY KEY失败，仅添加不带PK的id列
                    try:
                        add_id_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN id SERIAL"
                        cursor.execute(add_id_query)
                        print(f"✓ 成功添加id列到{table_name}表（不带PRIMARY KEY）")
                    except Exception as e:
                        print(f"✗ 添加id列到{table_name}表时出错: {e}")
            
            # 添加shipment_batch_no列（如果不存在）
            if 'shipment_batch_no' not in existing_columns:
                try:
                    add_batch_query = f"ALTER TABLE purchase_orders.{table_name} ADD COLUMN shipment_batch_no VARCHAR(50)"
                    cursor.execute(add_batch_query)
                    print(f"✓ 成功添加shipment_batch_no列到{table_name}表")
                except Exception as e:
                    print(f"✗ 添加shipment_batch_no列到{table_name}表时出错: {e}")
            else:
                print(f"✓ {table_name}表已经含有shipment_batch_no列")
    except Exception as e:
        print(f"✗ 处理closed表列時出错: {e}")

def add_timestamp_columns(cursor):
    """
    为所有采购订单表添加 created_at 和 update_at 字段
    """
    try:
        tables = ['wf_open', 'wf_closed', 'non_wf_open', 'non_wf_closed']
        
        for table_name in tables:
            # 检查列是否已存在
            check_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'purchase_orders' 
                AND table_name = %s 
                AND column_name IN ('created_at', 'update_at')
            """
            cursor.execute(check_columns_query, (table_name,))
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # 添加 created_at
            if 'created_at' not in existing_columns:
                try:
                    add_created_at_query = f"""
                        ALTER TABLE purchase_orders.{table_name} 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """
                    cursor.execute(add_created_at_query)
                    
                    # 为现有记录设置默认值（使用 po_placed_date 或当前时间）
                    update_existing_query = f"""
                        UPDATE purchase_orders.{table_name}
                        SET created_at = COALESCE(po_placed_date, CURRENT_TIMESTAMP)
                        WHERE created_at IS NULL
                    """
                    cursor.execute(update_existing_query)
                    print(f"✓ 成功添加 created_at 列到 {table_name} 表")
                except Exception as e:
                    print(f"✗ 添加 created_at 列到 {table_name} 表时出错: {e}")
            else:
                print(f"✓ {table_name} 表已经含有 created_at 列")
            
            # 添加 update_at
            if 'update_at' not in existing_columns:
                try:
                    add_update_at_query = f"""
                        ALTER TABLE purchase_orders.{table_name} 
                        ADD COLUMN update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """
                    cursor.execute(add_update_at_query)
                    print(f"✓ 成功添加 update_at 列到 {table_name} 表")
                except Exception as e:
                    print(f"✗ 添加 update_at 列到 {table_name} 表时出错: {e}")
            else:
                print(f"✓ {table_name} 表已经含有 update_at 列")
                
    except Exception as e:
        print(f"✗ 添加时间戳列时出错: {e}")

def create_update_timestamp_triggers(cursor):
    """
    创建触发器，在记录更新时自动更新 update_at 字段
    """
    try:
        # 创建触发器函数
        create_function_query = """
        CREATE OR REPLACE FUNCTION purchase_orders.update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.update_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        cursor.execute(create_function_query)
        print("✓ 成功创建 update_timestamp 函数")
        
        tables = ['wf_open', 'wf_closed', 'non_wf_open', 'non_wf_closed']
        for table_name in tables:
            try:
                # 删除旧触发器（如果存在）
                drop_trigger_query = f"""
                DROP TRIGGER IF EXISTS update_{table_name}_timestamp 
                ON purchase_orders.{table_name}
                """
                cursor.execute(drop_trigger_query)
                
                # 创建新触发器
                create_trigger_query = f"""
                CREATE TRIGGER update_{table_name}_timestamp
                BEFORE UPDATE ON purchase_orders.{table_name}
                FOR EACH ROW
                EXECUTE FUNCTION purchase_orders.update_timestamp()
                """
                cursor.execute(create_trigger_query)
                print(f"✓ 成功创建 update_at 触发器 for {table_name} 表")
            except Exception as e:
                print(f"✗ 创建触发器 for {table_name} 表时出错: {e}")
                
    except Exception as e:
        print(f"✗ 创建触发器函数时出错: {e}")

def fix_created_at_values(cursor):
    """
    修复现有记录的 created_at 值，使用 po_placed_date 作为真正的创建时间
    这个函数是幂等的，可以安全地多次运行
    """
    try:
        tables = ['wf_open', 'wf_closed', 'non_wf_open', 'non_wf_closed']
        
        for table_name in tables:
            try:
                # 更新 created_at 为 po_placed_date（如果 po_placed_date 不为空）
                update_query = f"""
                UPDATE purchase_orders.{table_name}
                SET created_at = po_placed_date
                WHERE po_placed_date IS NOT NULL 
                AND (created_at IS NULL OR created_at != po_placed_date)
                """
                cursor.execute(update_query)
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    print(f"✓ 成功修复 {table_name} 表的 {affected_rows} 条记录的 created_at 值")
                else:
                    print(f"✓ {table_name} 表的 created_at 值已经正确，无需修复")
            except Exception as e:
                print(f"✗ 修复 {table_name} 表的 created_at 值时出错: {e}")
                
    except Exception as e:
        print(f"✗ 修复 created_at 值时出错: {e}")

def create_users_table(cursor):
    """创建用户表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            is_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            token_expires TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON purchase_orders.users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_verification_token ON purchase_orders.users(verification_token)")
        
        print("✓ 成功创建用户表")
    except Exception as e:
        print(f"✗ 创建用户表时出错: {e}")

def create_po_records_table(cursor):
    """创建操作记录表"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS purchase_orders.po_records (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(20) NOT NULL,
            record_data JSONB NOT NULL,
            operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_records_user_email ON purchase_orders.po_records(user_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_records_table_name ON purchase_orders.po_records(table_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_records_operation ON purchase_orders.po_records(operation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_records_operation_time ON purchase_orders.po_records(operation_time)")
        
        print("✓ 成功创建操作记录表")
    except Exception as e:
        print(f"✗ 创建操作记录表时出错: {e}")

def main():
    """主函数"""
    print("开始初始化数据库...")
    print(f"数据库配置: host={os.getenv('DB_HOST', 'localhost')}, ")
    print(f"            db={os.getenv('DB_NAME', 'purchase_orders')}")
    print()
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 连接数据库
            db_config = get_db_config()
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            print("✓ 成功连接到数据库")
            print()
            
            # 创建模式和表
            create_purchase_orders_schema(cursor)
            create_wf_open_table(cursor)
            create_wf_closed_table(cursor)
            create_non_wf_open_table(cursor)
            create_non_wf_closed_table(cursor)
            create_users_table(cursor)
            create_po_records_table(cursor)
            add_shipment_batch_no_column(cursor)
            add_timestamp_columns(cursor)
            create_update_timestamp_triggers(cursor)
            fix_created_at_values(cursor)
            
            # 提交更改
            connection.commit()
            print()
            print("✓ 所有数据库对象创建完成")
            print()
            return True
            
        except psycopg2.OperationalError as e:
            retry_count += 1
            print(f"✗ 数据库连接失败 (尝试 {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                print(f"  {5}秒后重试...")
                import time
                time.sleep(5)
            else:
                print(f"✗ 无法连接到数据库，已放弃")
                return False
                
        except Exception as e:
            print(f"✗ 数据库初始化过程中出错: {e}")
            if 'connection' in locals():
                connection.rollback()
            return False
            
        finally:
            if 'connection' in locals() and connection:
                cursor.close()
                connection.close()

if __name__ == "__main__":
    main()