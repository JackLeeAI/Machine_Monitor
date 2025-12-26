from datetime import datetime
from models.user import User
from models.staff import Staff
from utils.logger import logger
from werkzeug.exceptions import BadRequest
from utils.db import get_db_connection


class AuthService:
    @staticmethod
    def login(username, password):
        """用户登录"""
        user = User.get_by_username(username)
        if not user:
            logger.warning(f"登录失败：用户名{username}不存在或已禁用")
            raise BadRequest("用户名不存在或已禁用")

        if not user.check_password(password):
            logger.warning(f"登录失败：用户{username}密码错误")
            raise BadRequest("密码错误")

        # 更新最后登录时间
        User.update_last_login(user.user_id)
        logger.info(f"用户{username}登录成功")
        return user

    @staticmethod
    def register(username, password, email, phone, position):
        """用户注册"""
        # 校验参数
        if not all([username, password, email, phone, position]):
            raise BadRequest("所有字段不能为空")

        if len(phone) != 11 or not phone.isdigit():
            raise BadRequest("手机号格式错误")

        # 校验用户名和职工是否已存在
        if User.get_by_username(username):
            raise BadRequest("用户名已存在")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 获取当前最大职工ID，为新记录生成ID
            cursor.execute("SELECT MAX(ID) FROM DEV.Dev_Person")
            max_id = cursor.fetchone()[0]
            person_id = max_id + 1 if max_id else 1
            
            # 先创建职工记录
            sql_staff = "INSERT INTO DEV.Dev_Person (ID, Name, Mail_Box, M_Tel, Per_pos) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(sql_staff, (person_id, username, email, phone, position))

            # 创建用户账号
            user = User(username=username, person_id=person_id, role=position)
            user.set_password(password)
            sql_user = "INSERT INTO DEV.Dev_Users (Username, Password, Person_ID, Role) VALUES (?, ?, ?, ?)"
            cursor.execute(sql_user, (username, user.password, person_id, position))
            
            # 获取用户ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            user_id = cursor.fetchone()[0]
            user.user_id = user_id
            
            # 统一提交事务
            conn.commit()

            logger.info(f"注册新用户：{username}（角色：{position}）")
            return user
        except Exception as e:
            # 发生错误时回滚事务
            conn.rollback()
            logger.error(f"用户注册失败：{str(e)}")
            raise BadRequest(f"注册失败：{str(e)}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_user_status(user_id, status):
        """启用/禁用用户"""
        return User.update_status(user_id, status)

    @staticmethod
    def get_all_users():
        """获取所有用户"""
        return User.get_all()