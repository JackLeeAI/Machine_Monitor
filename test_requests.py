# 只测试requests库的导入

print("开始测试...")

# 尝试导入内置模块，验证Python环境
import sys
print("Python版本：", sys.version)

# 尝试导入os模块
import os
print("当前工作目录：", os.getcwd())

# 尝试导入requests库
try:
    import requests
    print("✓ requests库已安装")
    print("版本：", requests.__version__)
    
    # 打印requests库的路径
    print("requests库路径：", requests.__file__)
    
except ImportError as e:
    print("✗ requests库未安装：", e)
except Exception as e:
    print("✗ 导入requests库时出错：", type(e).__name__, "-", e)
    import traceback
    traceback.print_exc()

print("测试结束")