import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_heartbeat_api():
    """测试心跳API"""
    url = 'http://localhost:5002/socket.io/?transport=polling&EIO=4'
    headers = {
        'Content-Type': 'text/plain'
    }
    
    try:
        # 1. 建立连接
        logger.info("建立Socket.IO连接")
        connect_payload = '40{"EIO":"4","transport":"polling"}'
        response = requests.post(url, data=connect_payload, headers=headers)
        logger.info(f"连接响应状态码: {response.status_code}")
        logger.info(f"连接响应内容: {response.text}")
        
        # 解析连接响应获取session ID
        if response.status_code == 200:
            connect_data = response.text
            # 提取session ID，格式类似: 0{"sid":"session_id",...}
            if connect_data.startswith('0'):
                connect_json = connect_data[1:]
                connect_info = json.loads(connect_json)
                sid = connect_info.get('sid')
                logger.info(f"获取到session ID: {sid}")
                
                if sid:
                    # 2. 发送心跳事件
                    logger.info("发送心跳事件")
                    heartbeat_url = f'{url}&sid={sid}'
                    heartbeat_payload = f'42["equipment_heartbeat",1]'
                    heartbeat_response = requests.post(heartbeat_url, data=heartbeat_payload, headers=headers)
                    logger.info(f"心跳响应状态码: {heartbeat_response.status_code}")
                    logger.info(f"心跳响应内容: {heartbeat_response.text}")
                    
                    # 3. 发送断开连接
                    logger.info("发送断开连接")
                    disconnect_payload = '41'
                    disconnect_response = requests.post(heartbeat_url, data=disconnect_payload, headers=headers)
                    logger.info(f"断开连接响应状态码: {disconnect_response.status_code}")
                    logger.info(f"断开连接响应内容: {disconnect_response.text}")
    
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("开始测试心跳API")
    test_heartbeat_api()
    logger.info("心跳API测试结束")