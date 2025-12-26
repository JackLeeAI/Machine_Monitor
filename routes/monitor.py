# routes/monitor.py
from flask import Blueprint, render_template, session, request, jsonify
from utils.auth import login_required  # 登录权限装饰器
from services.warning_service import WarningService  # 预警服务（原生SQL版）
from services.equipment_service import EquipmentService  # 设备服务（需确保为原生SQL版）
from services.workshop_service import WorkshopService  # 新增导入
import logging
from services.data_service import DataService
# 创建监控蓝图
monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')

# 配置日志
logger = logging.getLogger('utils.logger')


@monitor_bp.route('/realtime')
@login_required
def realtime():
    """
    实时监控页面（核心页面）
    - 展示所有设备在线状态
    - 统计待处理预警数量
    - 适配技术员/管理员权限
    - 添加分页功能，每页显示8个设备
    """
    try:
        # 1. 获取当前登录用户信息
        username = session.get('username')
        role = session.get('role', '技术员')

        # 2. 查询所有车间（新增：传递到模板）
        workshops = WorkshopService.get_all_workshops()  # 获取车间列表

        # 2. 添加分页功能
        page_param = request.args.get('page', '1')  # 获取当前页码，默认为'1'
        page = int(page_param) if page_param.strip() else 1  # 避免空字符串转换错误
        page_size = 8  # 每页显示8个设备

        # 3. 查询所有设备信息（适配原生SQL的EquipmentService，包含分页）
        equipments, equipment_count = EquipmentService.get_all_equipments(page=page, page_size=page_size)

        # 4. 查询待处理预警数量（修复后的WarningService，无ORM依赖）
        warning_count = len(WarningService.get_all_warnings(msg_state='待处理'))

        # 5. 统计在线/离线设备（假设设备表有Online_State字段）
        online_count = 0
        offline_count = 0
        for eq in equipments:
            if eq.online_status == '在线':
                online_count += 1
            else:
                offline_count += 1

        # 6. 计算总页数
        total_pages = (equipment_count + page_size - 1) // page_size  # 计算总页数
        
        # 确保页码在有效范围内
        page = max(1, min(page, total_pages))
        
        current_equipments = equipments  # 设备列表已经是分页后的结果

        # 6. 渲染页面（传递数据到模板）
        return render_template(
            'monitor/realtime.html',
            username=username,
            role=role,
            equipments=current_equipments,  # 传递当前页的设备列表
            equipment_count=equipment_count,
            online_count=online_count,
            offline_count=offline_count,
            warning_count=warning_count,
            workshops=workshops,  # 关键：传递车间列表
            page=page,  # 当前页码
            page_size=page_size,  # 每页显示数量
            total_pages=total_pages  # 总页数
        )
    except Exception as e:
        logger.error(f"加载实时监控页失败：{str(e)}")
        # 异常兜底：返回错误页面或跳转到首页
        return render_template('error.html', msg="加载实时监控数据失败，请稍后重试！"), 500


@monitor_bp.route('/warning/list')
@login_required
def warning_list():
    """
    预警列表页面
    - 展示所有预警（支持按状态筛选）
    """
    try:
        # 获取筛选条件（默认查询所有）
        msg_state = request.args.get('state', None)

        # 查询预警数据（原生SQL版）
        warnings = WarningService.get_all_warnings(msg_state=msg_state)

        # 渲染预警列表
        return render_template(
            'monitor/warning_list.html',
            warnings=warnings,
            current_state=msg_state or '全部'
        )
    except Exception as e:
        logger.error(f"加载预警列表失败：{str(e)}")
        return render_template('error.html', msg="加载预警数据失败！"), 500


@monitor_bp.route('/warning/update/<int:warning_id>', methods=['POST'])
@login_required
def update_warning(warning_id):
    """
    更新预警状态（AJAX接口）
    - 技术员可将预警标记为"已处理"
    """
    try:
        # 获取新状态（默认"已处理"）
        new_state = request.form.get('state', '已处理')

        # 调用服务更新状态
        result = WarningService.update_warning_state(warning_id, new_state)

        if result:
            logger.info(f"用户{session.get('username')}将预警{warning_id}更新为{new_state}")
            return jsonify({'code': 200, 'msg': '状态更新成功！'})
        else:
            return jsonify({'code': 500, 'msg': '状态更新失败！'})
    except Exception as e:
        logger.error(f"更新预警{warning_id}失败：{str(e)}")
        return jsonify({'code': 500, 'msg': '系统异常，更新失败！'})


@monitor_bp.route('/equipment/detail/<int:eq_id>')
@login_required
def equipment_detail(eq_id):
    """
    设备详情页面
    - 展示单台设备的实时数据、历史预警
    """
    try:
        # 查询设备详情
        equipment = EquipmentService.get_equipment_by_id(eq_id)
        if not equipment:
            return render_template('error.html', msg="设备不存在！"), 404

        # 查询该设备的历史预警
        warnings = WarningService.get_all_warnings(msg_state=None)
        eq_warnings = [w for w in warnings if w.Equipment_ID == eq_id]

        # 渲染设备详情
        return render_template(
            'monitor/equipment_detail.html',
            equipment=equipment,
            warnings=eq_warnings
        )
    except Exception as e:
        logger.error(f"加载设备{eq_id}详情失败：{str(e)}")
        return render_template('error.html', msg="加载设备详情失败！"), 500


# 在 monitor.py 中新增以下代码（放在现有路由之后）
@monitor_bp.route('/history')
@login_required
def history():
    """
    历史数据页面（适配模板中的 monitor.history 端点）
    - 展示设备历史采集数据、历史预警
    - 支持分页功能
    """
    try:
        # 1. 获取筛选条件（时间范围、监测点ID）
        start_date = request.args.get('start_time', '')
        end_date = request.args.get('end_time', '')
        mon_id = request.args.get('mon_id', '')
        
        # 2. 获取分页参数
        page = request.args.get('page', 1, type=int)
        page_size = 10

        # 3. 查询所有监测点（用于筛选下拉框）
        monitors = DataService.get_all_monitor_points()
        # 4. 查询历史数据（包含分页）
        history_data = DataService.get_history_data(start_date, end_date, mon_id)
        
        # 5. 实现分页逻辑
        total_count = len(history_data)
        total_pages = (total_count + page_size - 1) // page_size
        
        # 确保页码在有效范围内
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # 计算数据切片范围
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data = history_data[start_index:end_index]

        # 6. 渲染历史数据页面
        return render_template(
            'monitor/history.html',
            monitor_points=monitors,
            history_data=paginated_data,
            start_date=start_date,
            end_date=end_date,
            selected_mon_id=mon_id,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"加载历史数据页失败：{str(e)}")
        return render_template('error.html', msg="加载历史数据失败，请稍后重试！"), 500

@monitor_bp.route('/export_excel')
@login_required
def export_excel():
    """
    导出历史数据为Excel文件
    """
    try:
        import pandas as pd
        from io import BytesIO
        from datetime import datetime
        from flask import make_response
        import urllib.parse
        
        # 获取筛选条件（与history路由相同）
        start_date = request.args.get('start_time', '')
        end_date = request.args.get('end_time', '')
        mon_id = request.args.get('mon_id', '')
        
        # 查询历史数据
        history_data = DataService.get_history_data(start_date, end_date, mon_id)
        
        # 转换为pandas DataFrame
        df = pd.DataFrame(history_data)
        
        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='历史数据')
        
        # 设置响应头
        output.seek(0)
        filename = f'历史数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        # 创建响应对象
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # 修复文件名编码问题
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(filename)}'
        
        return response
    except Exception as e:
        logger.error(f"导出Excel失败：{str(e)}")
        return jsonify({'code': 500, 'msg': f'导出Excel失败：{str(e)}'})

@monitor_bp.route('/download_template')
@login_required
def download_template():
    """
    下载导入Excel模板
    """
    try:
        import pandas as pd
        from io import BytesIO
        from flask import make_response
        import urllib.parse
        
        # 创建模板DataFrame
        template_data = {
            '监测时间': ['2024-01-01 10:00:00', '2024-01-01 10:05:00'],
            '监测点名称': ['温度监测点', '湿度监测点'],
            '传感器类型': ['温度传感器', '湿度传感器'],
            '监测值': [25.5, 60.2],
            '单位': ['°C', '%RH'],
            '正常范围': ['20-30', '40-70'],
            '采集人': ['张三', '李四']
        }
        
        df = pd.DataFrame(template_data)
        
        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='导入模板')
        
        # 设置响应头
        output.seek(0)
        filename = '历史数据导入模板.xlsx'
        
        # 创建响应对象
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # 修复文件名编码问题
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(filename)}'
        
        return response
    except Exception as e:
        logger.error(f"下载模板失败：{str(e)}")
        return jsonify({'code': 500, 'msg': f'下载模板失败：{str(e)}'})

@monitor_bp.route('/import_excel', methods=['POST'])
@login_required
def import_excel():
    """
    导入Excel文件数据
    """
    try:
        import pandas as pd
        from datetime import datetime
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '请选择要上传的Excel文件'})
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'error': '请选择要上传的Excel文件'})
        
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 检查必要的列
        required_columns = ['监测时间', '监测点名称', '传感器类型', '监测值', '单位', '正常范围', '采集人']
        for col in required_columns:
            if col not in df.columns:
                return jsonify({'error': f'Excel文件缺少必要的列：{col}'})
        
        # 处理数据（这里仅作示例，实际需要根据数据库结构进行处理）
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # 解析监测时间
                mon_date = datetime.strptime(str(row['监测时间']), '%Y-%m-%d %H:%M:%S')
                
                # 这里需要根据实际数据库结构进行插入操作
                # 由于没有具体的数据库插入逻辑，这里仅作示例
                logger.info(f"处理第{index+1}行数据：{row['监测时间']} - {row['监测点名称']} - {row['监测值']}")
                
                success_count += 1
            except Exception as e:
                logger.error(f"处理第{index+1}行数据失败：{str(e)}")
                error_count += 1
        
        # 返回与前端期望一致的响应格式
        return jsonify({
            'success': success_count,
            'skipped': error_count
        })
    except Exception as e:
        logger.error(f"导入Excel失败：{str(e)}")
        return jsonify({'code': 500, 'msg': f'导入Excel失败：{str(e)}'})