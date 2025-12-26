from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService
from utils.auth import login_required
from werkzeug.exceptions import BadRequest
from models.user import User

# 移除：from utils.db import db （已无db实例）

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        try:
            user = AuthService.login(username, password)
            # 存储登录态到Session
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role
            session['person_id'] = user.person_id

            # 记录登录日志
            from models.early_warning import EarlyWarning
            warning_count = len(EarlyWarning.get_all(msg_state='待处理'))
            session['warning_count'] = warning_count

            flash(f'登录成功！欢迎{user.username}', 'success')
            return redirect(url_for('monitor.realtime'))
        except BadRequest as e:
            flash(str(e), 'error')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm_pwd = request.form.get('confirm_pwd').strip()
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()
        position = request.form.get('position').strip()

        # 基础校验
        if password != confirm_pwd:
            flash('两次密码不一致！', 'error')
            return render_template('auth/register.html')

        try:
            AuthService.register(username, password, email, phone, position)
            flash('注册成功！请使用新账号登录', 'success')
            return redirect(url_for('auth.login'))
        except BadRequest as e:
            flash(str(e), 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    # 记录退出日志（可选）
    session.clear()
    flash('已成功退出登录', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-pwd', methods=['GET', 'POST'])
@login_required
def change_pwd():
    """修改密码"""
    if request.method == 'POST':
        old_pwd = request.form.get('old_pwd').strip()
        new_pwd = request.form.get('new_pwd').strip()
        confirm_new_pwd = request.form.get('confirm_new_pwd').strip()

        # 校验
        if new_pwd != confirm_new_pwd:
            flash('两次新密码不一致！', 'error')
            return render_template('auth/change_pwd.html')
        if len(new_pwd) < 6:
            flash('新密码长度不能少于6位！', 'error')
            return render_template('auth/change_pwd.html')

        # 校验原密码并修改
        try:
            User.change_password(session['user_id'], old_pwd, new_pwd)
            flash('密码修改成功！请重新登录', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('auth/change_pwd.html')

    return render_template('auth/change_pwd.html')