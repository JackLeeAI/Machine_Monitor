from flask import Flask, redirect, url_for
from flask_socketio import SocketIO
from utils.logger import init_logger
from routes.auth import auth_bp
from routes.base_info import base_info_bp
from routes.monitor import monitor_bp
from routes.warning import warning_bp
from routes.system import system_bp
from utils.db import init_db
from config import SECRET_KEY, DEBUG, HEARTBEAT_TIMEOUT
import eventlet
from apscheduler.schedulers.background import BackgroundScheduler

# 解决 WebSocket 兼容性问题
eventlet.monkey_patch()

# 初始化日志
init_logger()

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# 方式1：直接设置debug（最简单）
app.debug = True
# 初始化数据库（纯原生 dmPython）
init_db()

# 注册所有蓝图
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(base_info_bp, url_prefix='/base_info')
app.register_blueprint(monitor_bp, url_prefix='/monitor')
app.register_blueprint(warning_bp, url_prefix='/warning')
app.register_blueprint(system_bp, url_prefix='/system')

# 初始化 WebSocket
socketio = SocketIO(app, cors_allowed_origins="*")

# 导入设备服务模块用于定时任务
from services.equipment_service import EquipmentService

# 创建定时任务调度器
scheduler = BackgroundScheduler()

# 添加定时任务，每隔HEARTBEAT_TIMEOUT秒检查一次设备在线状态
scheduler.add_job(func=EquipmentService.check_equipment_online_status, trigger='interval', seconds=HEARTBEAT_TIMEOUT)

# 启动定时任务调度器
scheduler.start()

# 首页重定向到登录页
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# WebSocket 设备心跳检测
@socketio.on('equipment_heartbeat')
def handle_heartbeat(equipment_id):
    print(f"收到设备心跳请求: {equipment_id}")
    from services.equipment_service import EquipmentService
    result = EquipmentService.update_equipment_heartbeat(equipment_id)
    print(f"心跳更新结果: {result}, 设备ID: {equipment_id}")
    socketio.emit('heartbeat_response', {'status': 'success', 'equipment_id': equipment_id})

if __name__ == "__main__":
    # 启动服务（支持 WebSocket）
    socketio.run(app, host='127.0.0.1', port=5002, debug=DEBUG)