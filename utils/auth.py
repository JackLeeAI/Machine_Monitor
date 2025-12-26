from flask import session, redirect, url_for, flash
from functools import wraps
import logging

# 配置日志
logger = logging.getLogger('utils.logger')

def login_required(f):
    """登录校验：未登录跳转到登录页"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 调试信息
        logger.info(f"===== login_required装饰器调用 =====")
        logger.info(f"当前session内容: {dict(session)}")
        logger.info(f"请求路径: {f.__name__}")
        
        if 'user_id' not in session:
            logger.info("未登录用户，重定向到登录页")
            flash('请先登录系统！', 'error')
            return redirect(url_for('auth.login'))
        logger.info(f"已登录用户: {session.get('username')}, 角色: {session.get('role')}")
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """管理员权限校验：非管理员无权限"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != '管理员':
            flash('仅管理员可执行此操作！', 'error')
            return redirect(url_for('monitor.realtime'))
        return f(*args, **kwargs)
    return wrapper