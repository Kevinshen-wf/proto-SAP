#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动入口
"""

import sys
import os
import subprocess

# 添加项目根目录到Python路径，以便正常导入模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from web_app import app

def initialize_database():
    """
    启动时尝试初始化数据库
    """
    print("[启动] 检查数据库初始化...")
    try:
        # 尝试执行init_db.py
        result = subprocess.run(
            ['python', 'init_db.py'],
            cwd=project_root,
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print("[启动] ✓ 数据库初始化成功")
            return True
        else:
            print(f"[启动] ✗ 数据库初始化失败: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"[启动] ✗ 初始化过程异常: {e}")
        return False

if __name__ == '__main__':
    # 启动时尝试初始化数据库
    print("\n" + "="*60)
    print("Proto-SAP Flask 应用启动")
    print("="*60 + "\n")
    
    initialize_database()
    
    print("\n" + "="*60)
    print("Flask 应用启动中...")
    print("="*60 + "\n")
    
    # 检查是否需要HTTPS
    use_ssl = os.getenv('USE_SSL', 'False').lower() == 'true'
    # 检查是否在Docker容器中运行（生产环境）
    in_docker = os.path.exists('/.dockerenv')
    # 获取debug模式：Docker中关闭debug，本地开发启用debug
    debug_mode = os.getenv('APP_DEBUG', str(not in_docker)).lower() == 'true'
    
    if use_ssl:
        # 生产环境：使用SSL
        # 需要提供证书文件
        cert_file = os.getenv('SSL_CERT_FILE', '/app/certs/cert.pem')
        key_file = os.getenv('SSL_KEY_FILE', '/app/certs/key.pem')
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            app.run(debug=False, host='0.0.0.0', port=5000, 
                   ssl_context=(cert_file, key_file), use_reloader=False)
        else:
            print(f"警告: SSL证书文件不存在")
            print(f"  证书: {cert_file}")
            print(f"  私钥: {key_file}")
            print(f"以HTTP模式运行...")
            app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=False)
    else:
        # 根据环境选择debug模式
        print(f"运行模式: {'开发模式（DEBUG=True，有自动重载）' if debug_mode else '生产模式（DEBUG=False，无自动重载）'}")
        print(f"Docker环境: {in_docker}")
        print()
        app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=debug_mode)
