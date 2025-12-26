# 检查 requests 模块的实际安装位置

import sys
print("Python版本：", sys.version)
print("Python路径：")
for path in sys.path:
    print("  ", path)

# 检查 requests 模块的安装位置
print("\n检查 requests 模块的安装位置：")
try:
    import requests
    print("requests 模块已找到！")
    print("版本：", requests.__version__)
    print("安装位置：", requests.__file__)
except ImportError:
    print("requests 模块未找到！")
    print("\n尝试使用 subprocess 安装并检查：")
    import subprocess
    # 尝试在当前 Python 环境中安装 requests
    result = subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True, text=True)
    print("安装输出：", result.stdout)
    if result.stderr:
        print("安装错误：", result.stderr)
    # 再次尝试导入
    try:
        import requests
        print("\n安装后成功导入 requests 模块！")
        print("版本：", requests.__version__)
        print("安装位置：", requests.__file__)
    except ImportError:
        print("\n安装后仍然无法导入 requests 模块！")
        print("请检查 Python 环境和路径设置。")