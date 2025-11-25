#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目启动脚本
用于检查环境并启动采购订单管理系统
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("✗ 错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✓ Python版本检查通过: {sys.version}")
    return True

def check_env_file():
    """检查.env文件是否存在"""
    if not os.path.exists('.env'):
        print("⚠ 警告: 未找到.env文件")
        print("请创建.env文件并配置数据库连接信息:")
        print("""
DB_HOST=localhost
DB_NAME=purchase_orders
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
        """)
        return False
    print("✓ 找到.env文件")
    return True

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        'flask',
        'psycopg2',
        'pdfplumber',
        'dotenv',
        'flask_cors'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            elif package == 'flask_cors':
                __import__('flask_cors')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("✗ 缺少必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✓ 所有依赖包检查通过")
    return True

def check_database_connection():
    """检查数据库连接"""
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'purchase_orders'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        connection = psycopg2.connect(**db_config)
        connection.close()
        print("✓ 数据库连接测试通过")
        return True
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        print("请检查.env文件中的数据库配置是否正确")
        return False

def check_upload_directory():
    """检查上传目录"""
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir)
            print(f"✓ 创建上传目录: {upload_dir}")
        except Exception as e:
            print(f"✗ 创建上传目录失败: {e}")
            return False
    else:
        print(f"✓ 上传目录已存在: {upload_dir}")
    return True

def main():
    """主函数"""
    print("=== 采购订单管理系统启动检查 ===\n")
    
    # 检查各项配置
    checks = [
        check_python_version,
        check_env_file,
        check_dependencies,
        check_database_connection,
        check_upload_directory
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()  # 添加空行分隔
    
    if not all_passed:
        print("✗ 系统检查未通过，请解决上述问题后重试")
        sys.exit(1)
    
    print("✓ 所有检查通过，正在启动系统...\n")
    
    # 启动Flask应用
    try:
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        app_path = os.path.join(backend_path, 'app.py')
        
        if not os.path.exists(app_path):
            print("✗ 未找到后端应用文件")
            sys.exit(1)
        
        print("启动Flask应用...")
        print("访问地址: http://localhost:5000")
        print("按 Ctrl+C 停止应用\n")
        
        # 程序底预上的上cd到项目根目录，声中准确构建的sys.path
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        
        try:
            # 启动应用
            subprocess.run([sys.executable, app_path], check=True)
        finally:
            os.chdir(original_cwd)
        
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"✗ 启动应用时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()