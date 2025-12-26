from flask import Blueprint, render_template, redirect, url_for, flash, session,request, jsonify
from services.auth_service import AuthService
from utils.auth import login_required, admin_required
from models.user import User
from models.staff import Staff
from models.early_warning import EarlyWarning
from models.workshop import Workshop
from models.equipment import Equipment
import hashlib

# 创建蓝图
system_bp = Blueprint('system', __name__, url_prefix='/system')


@system_bp.route('/user-manage')
@login_required
@admin_required
def user_manage():
    """用户账号管理"""
    users = AuthService.get_all_users()
    user_list = [user.to_dict() for user in users]

    # 统计用户状态
    enabled_count = len([u for u in user_list if u['status'] == '启用'])
    disabled_count = len([u for u in user_list if u['status'] == '禁用'])
    admin_count = len([u for u in user_list if u['role'] == '管理员'])
    tech_count = len([u for u in user_list if u['role'] == '技术员'])

    return render_template(
        'system/user_manage.html',
        users=user_list,
        enabled_count=enabled_count,
        disabled_count=disabled_count,
        admin_count=admin_count,
        tech_count=tech_count
    )


@system_bp.route('/update-user-status/<int:user_id>/<int:status>')
@login_required
@admin_required
def update_user_status(user_id, status):
    """启用/禁用用户"""
    try:
        AuthService.update_user_status(user_id, status)
        flash(f'用户已{"启用" if status == 1 else "禁用"}！', 'success')
    except Exception as e:
        flash(f'操作失败：{str(e)}', 'error')
    return redirect(url_for('system.user_manage'))


@system_bp.route('/log-list')
@login_required
@admin_required
def log_list():
    """系统操作日志"""
    # 此处简化实现（实际项目可扩展完整日志功能）
    logs = EarlyWarning.query.all()
    log_list = []
    for log in logs:
        log_list.append({
            'log_id': log.ID,
            'operate_time': log.Happen_Time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(log.Happen_Time, 'strftime') and log.Happen_Time else '',
            'operate_type': '预警生成',
            'operate_content': log.Msg_Text,
            'operator': log.handler_name if log.handler_name else '系统自动',
            'ip_address': '未知'
        })

    return render_template('system/log_list.html', logs=log_list)


@system_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """系统概览仪表盘"""
    # 统计数据
    user_count = User.query.count()
    workshop_count = Workshop.query.count()
    equipment_count = Equipment.query.count()
    online_equip_count = len(Equipment.query.filter_by(Online_Status='在线').all())
    warning_count = EarlyWarning.query.count()
    pending_warning_count = len(EarlyWarning.query.filter_by(Msg_State='待处理').all())

    # 设备在线率
    online_rate = (online_equip_count / equipment_count * 100) if equipment_count > 0 else 0

    # 预警状态统计
    processing_warning_count = len(EarlyWarning.query.filter_by(Msg_State='处理中').all())
    done_warning_count = len(EarlyWarning.query.filter_by(Msg_State='已处理').all())

    return render_template(
        'system/dashboard.html',
        user_count=user_count,
        workshop_count=workshop_count,
        equipment_count=equipment_count,
        online_equip_count=online_equip_count,
        online_rate=f'{online_rate:.1f}%',
        warning_count=warning_count,
        pending_warning_count=pending_warning_count,
        processing_warning_count=processing_warning_count,
        done_warning_count=done_warning_count
    )


# ========== 新增路由：user_add（新增用户） ==========
@system_bp.route('/user-add', methods=['GET', 'POST'])
@login_required
@admin_required
def user_add():
    if request.method == 'GET':
        # GET请求：渲染新增页面，获取所有职工列表用于下拉选择
        staffs = Staff.get_all()
        return render_template('system/user_add.html', staffs=staffs)

    # POST请求：处理表单提交
    try:
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        person_id = request.form.get('person_id', '').strip()
        role = request.form.get('role', '').strip()

        # 基础校验
        if not all([username, password, person_id, role]):
            flash('所有字段均为必填！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

        # 校验角色合法性
        if role not in ['管理员', '技术员']:
            flash('角色只能选择“管理员”或“技术员”！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

        # 校验职工ID是否存在
        if not Staff.get_by_id(person_id):
            flash(f'职工ID {person_id} 不存在！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

        # ========== 新增：校验职工ID是否已绑定其他用户 ==========
        if User.get_by_person_id(person_id):
            flash(f'职工ID {person_id} 已绑定其他用户，无法重复注册！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

        # 校验用户名是否重复
        if User.get_by_username(username):
            flash(f'用户名 {username} 已存在！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

        # 密码加密
        encrypted_pwd = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # 新增用户
        success = User.add(username, encrypted_pwd, person_id, role)
        if success:
            flash('用户新增成功！', 'success')
            return redirect(url_for('system.user_manage'))
        else:
            flash('用户新增失败！', 'error')
            staffs = Staff.get_all()
            return render_template('system/user_add.html', staffs=staffs)

    except Exception as e:
        print(f"新增用户报错：{str(e)}")
        flash(f'新增失败：{str(e)}', 'error')
        staffs = Staff.get_all()
        return render_template('system/user_add.html', staffs=staffs)


# ========== 新增路由：user_edit（编辑用户） ==========
@system_bp.route('/user-edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    # GET请求：渲染编辑页面，回显用户数据
    if request.method == 'GET':
        try:
            user = User.get_by_id(user_id)
            if not user:
                flash('用户不存在！', 'error')
                return redirect(url_for('system.user_manage'))
            # 转换为字典，避免递归
            user_data = user.to_dict(include_staff_detail=False)
            return render_template('system/user_edit.html', user=user_data)
        except Exception as e:
            print(f"加载编辑页面报错：{str(e)}")
            flash('加载用户信息失败！', 'error')
            return redirect(url_for('system.user_manage'))

    # POST请求：处理编辑提交
    try:
        # 获取表单数据
        role = request.form.get('role', '').strip()
        status = request.form.get('status', '1')  # 1=启用，0=禁用

        # 基础校验
        if not role:
            flash('角色为必填项！', 'error')
            return redirect(url_for('system.user_edit', user_id=user_id))

        # 校验角色合法性
        if role not in ['管理员', '技术员']:
            flash('角色只能选择“管理员”或“技术员”！', 'error')
            return redirect(url_for('system.user_edit', user_id=user_id))

        # 更新角色
        User.update_role(user_id, role)
        # 更新状态（转换为整数，处理空字符串情况）
        status_int = int(status) if status and status.strip() else 0
        User.update_status(user_id, status_int)

        flash('用户信息修改成功！', 'success')
        return redirect(url_for('system.user_manage'))

    except Exception as e:
        print(f"编辑用户报错：{str(e)}")
        flash(f'修改失败：{str(e)}', 'error')
        return redirect(url_for('system.user_edit', user_id=user_id))


# ========== 新增路由：user_delete（删除用户，可选） ==========
@system_bp.route('/user-delete/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def user_delete(user_id):
    try:
        # 1. 边界校验：用户ID有效性
        if user_id <= 0:
            flash('无效的用户ID！', 'error')
            return redirect(url_for('system.user_manage'))
        # 2. 校验用户是否存在（避免删除不存在的用户）
        if not User.get_by_id(user_id):
            flash(f'用户ID {user_id} 不存在，无需删除！', 'error')
            return redirect(url_for('system.user_manage'))

        # 3. 建立数据库连接并执行删除操作
        # 方式1：若你的User模型有封装delete方法（推荐）
        success = User.delete_by_id(user_id)
        if not success:
            flash(f'用户ID {user_id} 删除失败！', 'error')
            return redirect(url_for('system.user_manage'))

    except Exception as e:
        # 其他未知异常
        flash(f'删除失败：{str(e)}', 'error')
    return redirect(url_for('system.user_manage'))


@system_bp.route('/check-username')
@login_required
@admin_required
def check_username():
    """检查用户名是否存在（用于前端实时验证）"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'exists': False})
    
    try:
        user = User.get_by_username(username)
        return jsonify({'exists': user is not None})
    except Exception as e:
        print(f"检查用户名失败：{str(e)}")
        return jsonify({'exists': False})