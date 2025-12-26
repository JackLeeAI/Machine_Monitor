import socketio
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Socket.IO客户端实例
sio = socketio.Client()

sio.logger = logger
sio.engineio_logger = logger

# 连接事件处理器
@sio.event
def connect():
    logger.info("成功连接到服务器")
    
    # 发送设备1的心跳
    equipment_id = 1
    logger.info(f"发送设备 {equipment_id} 的心跳")
    sio.emit('equipment_heartbeat', equipment_id)
    logger.info(f"设备 {equipment_id} 的心跳发送完成")
    
    # 等待2秒，然后断开连接
    time.sleep(2)
    logger.info("断开连接")
    sio.disconnect()

# 心跳响应事件处理器
@sio.event
def heartbeat_response(data):
    logger.info(f"收到心跳响应: {data}")

# 连接错误事件处理器
@sio.event
def connect_error(e):
    logger.error(f"连接错误: {e}")

# 断开连接事件处理器
@sio.event
def disconnect():
    logger.info("与服务器断开连接")

# 运行客户端
if __name__ == "__main__":
    try:
        logger.info("启动心跳测试客户端")
        logger.info("尝试连接到服务器 http://localhost:5002")
        sio.connect('http://localhost:5002')
        logger.info("连接请求已发送")
        
        # 保持程序运行，直到连接断开
        sio.wait()
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)