# 检查 Python 路径和包的安装位置

import sys
print("Python版本：", sys.version)
print("Python路径：")
for path in sys.path:
    print("  ", path)

# 检查 pip 安装的包
print("\n使用 pip list 查看已安装的包：")
import subprocess
result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
print(result.stdout)

if result.stderr:
    print("\npip list 错误：")
    print(result.stderr)

# 尝试直接执行 pip install requests
print("\n尝试直接执行 pip install requests：")
result = subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True, text=True)
print(result.stdout)

if result.stderr:
    print("\npip install 错误：")
    print(result.stderr)