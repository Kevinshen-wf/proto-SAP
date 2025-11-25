#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动入口
"""

import sys
import os

# 添加项目根目录到Python路径，以便正常导入模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from web_app import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
