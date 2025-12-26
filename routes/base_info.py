from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.equipment_service import EquipmentService
from models.workshop import Workshop
from models.equipment import Equipment
from models.equipment_part import EquipmentPart
from utils.auth import login_required, admin_required
from werkzeug.exceptions import BadRequest
from datetime import datetime

# 创建蓝图（前缀统一为 /base-info，适配前端路由）
base_info_bp = Blueprint('base_info', __name__, url_prefix='/base-info')


# ---------------------- 基础信息主页面 ----------------------
@base_info_bp.route('/')
@login_required
def base_info_main():
    """基础信息主页面，展示模块概览和统计信息"""
    from models.equipment import Equipment
    from models.equipment_part import EquipmentPart
    
    # 获取统计数据
    workshop_count = len(EquipmentService.get_all_workshops())
    equipment_count = Equipment.count_all()
    online_count = Equipment.count_online()
    part_count = EquipmentPart.count_all()
    
    return render_template('base_info/base_info_main.html', 
                          workshop_count=workshop_count,
                          equipment_count=equipment_count,
                          online_count=online_count,
                          part_count=part_count)


# ---------------------- 车间管理 ----------------------
@base_info_bp.route('/workshop')
@login_required
def workshop_list():
    """车间列表（关联设备数量统计，适配表0.2+表0.3）"""
    workshops = EquipmentService.get_all_workshops()
    workshop_data = []
    for ws in workshops:
        # 调用模型原生方法查询，替代ORM
        equip_count = len(Equipment.get_by_workshop_id(ws.id))
        workshop_data.append({
            'workshop': ws,
            'equip_count': equip_count
        })
    return render_template('base_info/workshop_list_new.html', workshop_data=workshop_data)


@base_info_bp.route('/workshop/add', methods=['GET', 'POST'])
@login_required
@admin_required
def workshop_add():
    """新增车间（适配表0.2，纯原生SQL实现）"""

    if request.method == 'POST':
        workshop_name = request.form.get('workshop_name').strip()
        if not workshop_name:
            flash('车间名称不能为空！', 'error')
            return render_template('base_info/workshop_add.html')

        # 校验重复（调用模型方法）
        if Workshop.get_by_name(workshop_name):
            flash('该车间已存在！', 'error')
            return render_template('base_info/workshop_add.html')

        # 新增车间（调用模型add方法）
        try:
            Workshop.add(workshop_name)
            flash('车间新增成功！', 'success')
            return redirect(url_for('base_info.workshop_list'))
        except Exception as e:
            flash(f'新增失败：{str(e)}', 'error')
            return render_template('base_info/workshop_add.html')

    return render_template('base_info/workshop_add.html')


@base_info_bp.route('/workshop/edit/<int:workshop_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def workshop_edit(workshop_id):

    workshop = Workshop.get_by_id(workshop_id)
    if not workshop:
        flash('车间不存在！', 'error')
        return redirect(url_for('base_info.workshop_list'))

    if request.method == 'POST':
        new_name = request.form.get('workshop_name', '').strip()
        if not new_name:
            flash('车间名称不能为空！', 'error')
            return render_template('base_info/workshop_edit.html', workshop=workshop)

        # 校验名称唯一
        if Workshop.get_by_name(new_name) and Workshop.get_by_name(new_name).id != workshop_id:
            flash('该车间名称已被使用！', 'error')
            return render_template('base_info/workshop_edit.html', workshop=workshop)

        # 更新车间（调用模型update方法）
        try:
            Workshop.update(workshop_id, new_name)
            flash('车间修改成功！', 'success')
            return redirect(url_for('base_info.workshop_list'))
        except Exception as e:
            flash(f'修改失败：{str(e)}', 'error')
            return render_template('base_info/workshop_edit.html', workshop=workshop)

    return render_template('base_info/workshop_edit.html', workshop=workshop)


@base_info_bp.route('/workshop/delete/<int:workshop_id>')
@login_required
@admin_required
def workshop_delete(workshop_id):
    """删除车间"""
    print(f"===== 开始执行workshop_delete，ID：{workshop_id} =====")
    workshop = Workshop.get_by_id(workshop_id)
    if not workshop:
        flash('车间不存在！', 'error')
        return redirect(url_for('base_info.workshop_list'))

    # 校验关联设备
    if Equipment.get_by_workshop_id(workshop_id):
        flash('该车间下有关联设备，无法删除！', 'error')
        return redirect(url_for('base_info.workshop_list'))

    # 删除车间（调用模型delete方法）
    try:
        Workshop.delete(workshop_id)
        flash('车间删除成功！', 'success')
        return redirect(url_for('base_info.workshop_list'))
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'error')
        return redirect(url_for('base_info.workshop_list'))


# ---------------------- 设备管理 ----------------------
@base_info_bp.route('/equipment')
@login_required
def equipment_list():
    """设备列表（支持筛选和分页，适配表0.3）"""
    workshop_id = request.args.get('workshop_id')
    use_state = request.args.get('use_state')
    page = request.args.get('page', 1, type=int)
    page_size = 10  # 每页显示10条
    
    # 修复：确保workshop_id不是空字符串
    if workshop_id == '':
        workshop_id = None

    # 获取设备列表和总数（支持分页）
    equipments, total_count = EquipmentService.get_all_equipments(
        workshop_id=workshop_id,
        use_state=use_state,
        page=page,
        page_size=page_size
    )
    workshops = EquipmentService.get_all_workshops()

    # 转换为字典格式，便于前端渲染
    equip_list = [eq.to_dict() for eq in equipments]

    # 计算总页数
    total_pages = (total_count + page_size - 1) // page_size

    return render_template(
        'base_info/equipment_list_new.html',
        equipments=equip_list,
        workshops=workshops,
        selected_workshop=workshop_id,
        selected_use_state=use_state,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_count=total_count
    )


@base_info_bp.route('/equipment/detail/<int:eq_id>')
@login_required
def equipment_detail(eq_id):
    """设备详情（修复URL格式：< → <）"""
    equipment = EquipmentService.get_equipment_by_id(eq_id)
    parts = EquipmentService.get_equipment_parts(eq_id)

    # 获取设备关联的监测点和最新数据
    from services.data_service import DataService
    monitor_points = DataService.get_monitor_points_by_equipment_id(equipment_id=eq_id)
    print(f"设备{eq_id}的监测点列表：{[p.name for p in monitor_points]}")  # 优化打印，便于调试

    latest_data = {}
    for point in monitor_points:
        # a = point.to_dict()
        # print(a)
        data = DataService.get_latest_data_by_monitor_point(point.id)
        latest_data[point.id] = data.to_dict() if data else None
    return render_template(
        'base_info/equipment_detail.html',
        equipment=equipment.to_dict(),
        parts=[p.to_dict() for p in parts],
        monitor_points=[p.to_dict() for p in monitor_points],
        latest_data=latest_data
    )


@base_info_bp.route('/equipment/add', methods=['GET', 'POST'])
@login_required
@admin_required
def equipment_add():
    """新增设备（适配表0.3，纯原生实现）"""
    workshops = EquipmentService.get_all_workshops()
    from models.staff import Staff
    staffs = Staff.get_all()  # 负责人列表（调用模型原生方法）

    if request.method == 'POST':
        equip_code = request.form.get('equip_code').strip()
        name = request.form.get('name').strip()
        pos_id = request.form.get('pos_id')
        person_id = request.form.get('person_id')
        pur_date = request.form.get('pur_date')
        first_time = request.form.get('first_time')
        use_state = request.form.get('use_state', '在用')

        # 校验必填字段
        if not all([equip_code, name, pos_id, person_id, pur_date, first_time]):
            flash('所有带*字段不能为空！', 'error')
            return render_template('base_info/equipment_add.html', workshops=workshops, staffs=staffs)

        # 校验日期格式
        try:
            datetime.strptime(pur_date, '%Y-%m-%d')
            datetime.strptime(first_time, '%Y-%m-%d')
        except ValueError:
            flash('日期格式错误！请使用YYYY-MM-DD格式', 'error')
            return render_template('base_info/equipment_add.html', workshops=workshops, staffs=staffs)

        # 校验设备编码唯一
        if Equipment.get_by_equip_code(equip_code):
            flash('设备编码已存在！', 'error')
            return render_template('base_info/equipment_add.html', workshops=workshops, staffs=staffs)

        # 新增设备（调用模型add方法）
        try:
            Equipment.add(
                equip_code=equip_code,
                name=name,
                pos_id=pos_id,
                person_id=person_id,
                pur_date=pur_date,
                first_time=first_time,
                use_state=use_state
            )
            flash('设备新增成功！', 'success')
            return redirect(url_for('base_info.equipment_list'))
        except Exception as e:
            flash(f'新增失败：{str(e)}', 'error')
            return render_template('base_info/equipment_add.html', workshops=workshops, staffs=staffs)

    return render_template('base_info/equipment_add.html', workshops=workshops, staffs=staffs)


@base_info_bp.route('/equipment/edit/<int:eq_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def equipment_edit(eq_id):
    """编辑设备（修复URL格式：< → <）"""
    equipment = EquipmentService.get_equipment_by_id(eq_id)
    workshops = EquipmentService.get_all_workshops()
    from models.staff import Staff
    staffs = Staff.get_all()

    if request.method == 'POST':
        name = request.form.get('name').strip()
        pos_id = request.form.get('pos_id')
        person_id = request.form.get('person_id')
        pur_date = request.form.get('pur_date')
        first_time = request.form.get('first_time')
        use_state = request.form.get('use_state')

        # 校验必填字段
        if not all([name, pos_id, person_id, pur_date, first_time]):
            flash('所有带*字段不能为空！', 'error')
            return render_template('base_info/equipment_edit.html', equipment=equipment, workshops=workshops,
                                   staffs=staffs)

        # 校验日期格式
        try:
            datetime.strptime(pur_date, '%Y-%m-%d')
            datetime.strptime(first_time, '%Y-%m-%d')
        except ValueError:
            flash('日期格式错误！', 'error')
            return render_template('base_info/equipment_edit.html', equipment=equipment, workshops=workshops,
                                   staffs=staffs)

        # 更新设备信息（调用模型update方法）
        try:
            Equipment.update(
                equipment_id=eq_id,
                name=name,
                pos_id=pos_id,
                person_id=person_id,
                pur_date=pur_date,
                first_time=first_time,
                use_state=use_state
            )
            flash('设备修改成功！', 'success')
            return redirect(url_for('base_info.equipment_detail', eq_id=eq_id))
        except Exception as e:
            flash(f'修改失败：{str(e)}', 'error')
            return render_template('base_info/equipment_edit.html', equipment=equipment, workshops=workshops,
                                   staffs=staffs)

    return render_template(
        'base_info/equipment_edit.html',
        equipment=equipment,
        workshops=workshops,
        staffs=staffs
    )


@base_info_bp.route('/equipment/delete/<int:eq_id>')
@login_required
@admin_required
def equipment_delete(eq_id):
    """删除设备（修复URL格式：< → <）"""
    equipment = EquipmentService.get_equipment_by_id(eq_id)
    if not equipment:
        flash('设备不存在！', 'error')
        return redirect(url_for('base_info.equipment_list'))

    # 校验关联部件
    parts, _ = EquipmentPart.get_all(equipment_id=eq_id)
    if parts:
        flash('该设备下有关联部件，无法删除！', 'error')
        return redirect(url_for('base_info.equipment_list'))

    # 删除设备（调用模型delete方法）
    try:
        Equipment.delete(eq_id)
        flash('设备删除成功！', 'success')
        return redirect(url_for('base_info.equipment_list'))
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'error')
        return redirect(url_for('base_info.equipment_list'))


# ---------------------- 部件管理 ----------------------
@base_info_bp.route('/part')
@login_required
def part_list():
    """部件列表（适配表0.4，支持分页）"""
    equipment_id = request.args.get('equipment_id')
    page = request.args.get('page', 1, type=int)
    page_size = 10  # 每页显示10条记录
    equipments = Equipment.get_all()  # 调用模型原生方法

    # 获取部件列表和总数（支持分页）
    if equipment_id:
        parts, total_count = EquipmentPart.get_all(equipment_id=equipment_id, page=page, page_size=page_size)
    else:
        parts, total_count = EquipmentPart.get_all(page=page, page_size=page_size)

    # 计算总页数
    total_pages = (total_count + page_size - 1) // page_size

    # 计算页码范围
    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)

    return render_template(
        'base_info/part_list_new.html',
        parts=[p.to_dict() for p in parts],
        equipments=equipments,
        selected_equipment=equipment_id,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_count=total_count,
        start_page=start_page,
        end_page=end_page
    )


@base_info_bp.route('/part/add', methods=['GET', 'POST'])
@login_required
@admin_required
def part_add():
    """新增部件（适配表0.4）"""
    # 获取所有设备，不使用分页
    equipments, _ = Equipment.get_all(page=1, page_size=1000)
    if request.method == 'POST':
        mid = request.form.get('mid')
        part_name = request.form.get('part_name').strip()
        description = request.form.get('description').strip()

        if not all([mid, part_name]):
            flash('设备和部件名称不能为空！', 'error')
            return render_template('base_info/part_add.html', equipments=equipments)

        # 校验同一设备下部件名称唯一
        if EquipmentPart.get_by_equipment_and_name(mid, part_name):
            flash('该设备下已存在同名部件！', 'error')
            return render_template('base_info/part_add.html', equipments=equipments)

        # 新增部件（调用模型add方法）
        try:
            EquipmentPart.add(
                mid=mid,
                part_name=part_name,
                description=description
            )
            flash('部件新增成功！', 'success')
            return redirect(url_for('base_info.part_list'))
        except Exception as e:
            flash(f'新增失败：{str(e)}', 'error')
            return render_template('base_info/part_add.html', equipments=equipments)

    return render_template('base_info/part_add.html', equipments=equipments)


@base_info_bp.route('/part/edit/<int:part_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def part_edit(part_id):
    """编辑部件（修复URL格式+模板路径错误）"""
    part = EquipmentPart.get_by_id(part_id)
    equipments = Equipment.get_all()
    if not part:
        flash('部件不存在！', 'error')
        return redirect(url_for('base_info.part_list'))

    if request.method == 'POST':
        mid = request.form.get('mid')
        part_name = request.form.get('part_name').strip()
        description = request.form.get('description').strip()

        if not all([mid, part_name]):
            flash('设备和部件名称不能为空！', 'error')
            # 修复模板路径：base_info.part_edit → base_info/part_edit.html
            return render_template('base_info/part_edit.html', part=part, equipments=equipments)

        # 校验唯一
        if EquipmentPart.get_by_equipment_and_name(mid, part_name) and EquipmentPart.get_by_equipment_and_name(mid,
                                                                                                               part_name).id != part_id:
            flash('该设备下已存在同名部件！', 'error')
            return render_template('base_info/part_edit.html', part=part, equipments=equipments)

        # 更新部件（调用模型update方法）
        try:
            EquipmentPart.update(
                part_id=part_id,
                mid=mid,
                part_name=part_name,
                description=description
            )
            flash('部件修改成功！', 'success')
            return redirect(url_for('base_info.part_list'))
        except Exception as e:
            flash(f'修改失败：{str(e)}', 'error')
            return render_template('base_info/part_edit.html', part=part, equipments=equipments)

    return render_template('base_info/part_edit.html', part=part, equipments=equipments)


@base_info_bp.route('/part/delete/<int:part_id>')
@login_required
@admin_required
def part_delete(part_id):
    """删除部件（修复URL格式：< → <）"""
    part = EquipmentPart.get_by_id(part_id)
    if not part:
        flash('部件不存在！', 'error')
        return redirect(url_for('base_info.part_list'))

    # 校验关联监测点
    from models.monitor_point import MonitorPoint
    if MonitorPoint.get_by_part_id(part_id):
        flash('该部件下有关联监测点，无法删除！', 'error')
        return redirect(url_for('base_info.part_list'))

    # 删除部件（调用模型delete方法）
    try:
        EquipmentPart.delete(part_id)
        flash('部件删除成功！', 'success')
        return redirect(url_for('base_info.part_list'))
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'error')
        return redirect(url_for('base_info.part_list'))