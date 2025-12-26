from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from services.warning_service import WarningService
from utils.auth import login_required
from datetime import datetime
from models.early_warning import EarlyWarning
from models.staff import Staff
from utils.db import get_db_connection

# 创建蓝图
warning_bp = Blueprint('warning', __name__, url_prefix='/warning')


@warning_bp.route('/list')
@login_required
def warning_list():
    """预警信息列表"""
    # 获取筛选参数
    msg_state = request.args.get('msg_state')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    # 时间处理
    start_date = datetime.strptime(start_time, '%Y-%m-%d') if start_time else None
    end_date = datetime.strptime(end_time, '%Y-%m-%d').replace(hour=23, minute=59, second=59) if end_time else None

    # 查询预警数据
    warnings = WarningService.get_all_warnings(
        msg_state=msg_state,
        start_time=start_date,
        end_time=end_date
    )
    warning_list = [warn.to_dict() for warn in warnings]

    # 统计各状态预警数
    total_count = len(warning_list)
    pending_count = len([w for w in warning_list if w['msg_state'] == '待处理'])
    processing_count = len([w for w in warning_list if w['msg_state'] == '处理中'])
    done_count = len([w for w in warning_list if w['msg_state'] == '已处理'])

    return render_template(
        'warning/warning_list.html',
        warnings=warning_list,
        selected_state=msg_state,
        selected_start=start_time,
        selected_end=end_time,
        total_count=total_count,
        pending_count=pending_count,
        processing_count=processing_count,
        done_count=done_count
    )


@warning_bp.route('/handle/<int:warn_id>', methods=['GET', 'POST'])
@login_required
def warning_handle(warn_id):
    """处理预警"""
    # 使用原生SQL查询预警信息
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ID, Mon_ID, Msg_Text, Per_ID, Msg_State, Happen_Time, Handle_Time FROM DEV.DEV_WARNING WHERE ID = ?", (warn_id,))
        row = cursor.fetchone()
        if not row:
            flash('预警不存在！', 'error')
            return redirect(url_for('warning.warning_list'))
        
        # 封装为EarlyWarning对象
        warning = EarlyWarning(
            id=row[0],
            mon_id=row[1],
            msg_text=row[2],  # 预警内容
            per_id=row[3],
            msg_state=row[4],
            happen_time=row[5],
            handle_time=row[6]
        )
    finally:
        cursor.close()
        conn.close()
    
    # 获取所有人员列表
    staff_list = Staff.get_all_staff()
    staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]

    if request.method == 'POST':
        handle_note = request.form.get('handle_note').strip()
        handle_state = request.form.get('handle_state')

        if not handle_note:
            flash('处理备注不能为空！', 'error')
            # 获取所有人员列表
            staff_list = Staff.get_all_staff()
            staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]
            return render_template('warning/warning_handle.html', warning=warning.to_dict(), staff_list=staff_dict)

        handler_id = request.form.get('handler')  # 使用正确的表单字段名
        print(handler_id)
        if not handler_id:
            flash('请选择处理人！', 'error')
            # 获取所有人员列表
            staff_list = Staff.get_all_staff()
            staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]
            return render_template('warning/warning_handle.html', warning=warning.to_dict(), staff_list=staff_dict)

        try:
            # 更新预警状态
            success = WarningService.update_warning_state(
                warning_id=warn_id,
                new_state=handle_state,
                handle_remark=handle_note,
                handler_id=handler_id,
                handle_time=datetime.now()
            )
            print(success)
            if success:
                flash('预警处理成功！', 'success')
                return redirect(url_for('warning.warning_list'))
            else:
                flash('处理失败：更新预警状态失败', 'error')
            # 获取所有人员列表
            staff_list = Staff.get_all_staff()
            staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]
            return render_template('warning/warning_handle.html', warning=warning.to_dict(), staff_list=staff_dict)
        except Exception as e:
            flash(f'处理失败：{str(e)}', 'error')
            # 获取所有人员列表
            staff_list = Staff.get_all_staff()
            staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]
            return render_template('warning/warning_handle.html', warning=warning.to_dict(), staff_list=staff_dict)

    # 获取所有人员列表
    staff_list = Staff.get_all_staff()
    staff_dict = [{'ID': staff.id, 'Staff_Name': staff.name} for staff in staff_list]
    
    return render_template('warning/warning_handle.html', warning=warning.to_dict(), staff_list=staff_dict)


@warning_bp.route('/cancel/<int:warn_id>')
@login_required
def warning_cancel(warn_id):
    """取消预警（仅管理员可操作）"""
    if not session.get('is_admin'):
        flash('权限不足！', 'error')
        return redirect(url_for('warning.warning_list'))

    try:
        # 使用原生SQL删除预警记录
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM DEV.DEV_WARNING WHERE ID = ?", (warn_id,))
            if cursor.rowcount == 0:
                flash('预警不存在！', 'error')
                return redirect(url_for('warning.warning_list'))
            conn.commit()
            flash('预警取消成功！', 'success')
            return redirect(url_for('warning.warning_list'))
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        flash(f'取消失败：{str(e)}', 'error')
        return redirect(url_for('warning.warning_list'))