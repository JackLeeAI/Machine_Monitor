import socketio
import time
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)  # 提高日志级别
logger = logging.getLogger(__name__)

# 创建Socket.IO客户端实例，启用日志
sio = socketio.Client(logger=True, engineio_logger=True)

# 设备ID列表（只测试设备1）
equipment_ids = [1]

# 连接事件处理器
@sio.event
def connect():
    logger.info("Connected to server")
    # 连接成功后立即发送心跳
    send_heartbeat()

# 心跳响应事件处理器
@sio.event
def heartbeat_response(data):
    logger.info(f"Heartbeat response received: {data}")

# 断开连接事件处理器
@sio.event
def disconnect():
    logger.info("Disconnected from server")

# 连接错误事件处理器
@sio.event
def connect_error(e):
    logger.error(f"Connection error: {e}")

# 发送心跳函数
def send_heartbeat():
    for equipment_id in equipment_ids:
        logger.info(f"Sending heartbeat for equipment {equipment_id}")
        try:
            sio.emit('equipment_heartbeat', equipment_id)
            logger.info(f"Heartbeat sent successfully for equipment {equipment_id}")
        except Exception as e:
            logger.error(f"Failed to send heartbeat for equipment {equipment_id}: {e}")
        time.sleep(0.5)  # 等待0.5秒，避免请求过于密集

if __name__ == "__main__":
    try:
        logger.info("Starting test heartbeat client")
        logger.info("Attempting to connect to server...")
        # 连接到服务器，使用轮询传输
        sio.connect('http://localhost:5002', transports=['polling'])
        
        logger.info("Connected to server")
        
        # 保持连接一段时间，看看是否能收到响应
        time.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        logger.info("Disconnecting from server")
        # 断开连接
        sio.disconnect()
        logger.info("Test completed")