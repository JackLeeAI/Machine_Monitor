# 测试脚本：验证requests和socketio库的安装状态

try:
    import requests
    print("✓ requests库已安装")
    print("  版本：", requests.__version__)
    print("  基本功能：")
    # 测试requests的基本功能
    response = requests.get("https://www.example.com")
    print("    ✓ 可以发送HTTP请求")
    print("    响应状态码：", response.status_code)
except ImportError:
    print("✗ requests库未安装")
except Exception as e:
    print("✗ requests库有问题：", e)

try:
    import socketio
    print("✓ socketio库已安装")
    
    # 测试socketio的基本功能
    try:
        from socketio import Client
        print("  ✓ socketio.Client可用")
        sio = Client()
        print("  ✓ 可以创建Client实例")
    except Exception as e:
        print("  ✗ socketio.Client不可用：", e)
        
    # 检查socketio的传输方式
    try:
        print("  socketio支持的传输方式：", socketio.transports)
    except Exception as e:
        print("  ✗ 无法获取传输方式：", e)
except ImportError:
    print("✗ socketio库未安装")
except Exception as e:
    print("✗ socketio库有问题：", e)