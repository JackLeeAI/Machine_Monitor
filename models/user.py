from utils.db import get_db_connection
from datetime import datetime
import hashlib


class User:
    def __init__(self, user_id=None, username=None, password=None, person_id=None, role=None, create_time=None,
                 last_login=None, status=1):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.person_id = person_id
        self.role = role
        self.create_time = create_time
        self.last_login = last_login
        self.status = status  # 1=启用，0=禁用

    def set_password(self, password):
        """密码加密（SHA-256）"""
        self.password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        """密码校验（修复硬编码问题）"""
        if not self.password:
            return False
        # 移除硬编码，使用传入的密码进行校验
        encrypted_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return self.password == encrypted_input

    def to_dict(self, include_staff_detail=False):
        """
        转换为字典（修复循环递归问题）
        :param include_staff_detail: 是否包含职工详情（False=仅基础信息，避免递归）
        """
        # 基础用户信息（无递归）
        base_data = {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'person_id': self.person_id,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.create_time, 'strftime') and self.create_time else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.last_login, 'strftime') and self.last_login else '未登录',
            'status': '启用' if self.status == 1 else '禁用'
        }

        # 仅在需要时返回职工基础信息，避免调用staff.to_dict()
        if include_staff_detail and self.person_id:
            try:
                from models.staff import Staff
                staff = Staff.get_by_id(self.person_id)
                if staff:
                    # 只返回职工基础字段，不调用staff.to_dict()，避免递归
                    base_data['staff_info'] = {
                        'id': staff.id,
                        'name': staff.name,
                        'department': staff.department,
                        'phone': staff.phone
                    }
                else:
                    base_data['staff_info'] = {}
            except Exception:
                base_data['staff_info'] = {}
        else:
            # 不返回staff_info或仅返回ID，彻底避免递归
            base_data['staff_id'] = self.person_id

        return base_data

    @staticmethod
    def get_by_username(username):
        """根据用户名查询用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            SELECT User_ID, Username, Password, Person_ID, Role, Create_Time, Last_Login, Status 
            FROM DEV.Dev_Users 
            WHERE Username = ? AND Status = 1
            """
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row[0],
                username=row[1],
                password=row[2],
                person_id=row[3],
                role=row[4],
                create_time=row[5],
                last_login=row[6],
                status=row[7]
            )
        except Exception as e:
            print(f"查询用户失败（用户名：{username}）：{str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_by_person_id(person_id):
        """根据职工ID查询用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            SELECT User_ID, Username, Password, Person_ID, Role, Create_Time, Last_Login, Status 
            FROM DEV.Dev_Users 
            WHERE Person_ID = ?
            """
            cursor.execute(sql, (person_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row[0],
                username=row[1],
                password=row[2],
                person_id=row[3],
                role=row[4],
                create_time=row[5],
                last_login=row[6],
                status=row[7]
            )
        except Exception as e:
            print(f"查询用户失败（职工ID：{person_id}）：{str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def register(username, password, person_id, role):
        """用户注册（添加异常处理）"""
        # 先校验职工是否存在
        try:
            from models.staff import Staff
            if not Staff.get_by_id(person_id):
                raise ValueError(f"职工ID={person_id}不存在，无法注册用户")

            # 校验用户名是否重复
            if User.get_by_username(username):
                raise ValueError(f"用户名{username}已存在")

            conn = get_db_connection()
            cursor = conn.cursor()
            # 密码加密
            encrypted_pwd = hashlib.sha256(password.encode('utf-8')).hexdigest()
            sql = """
            INSERT INTO DEV.Dev_Users (Username, Password, Person_ID, Role, Create_Time) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            cursor.execute(sql, (username, encrypted_pwd, person_id, role))
            conn.commit()
            return True
        except ValueError as e:
            print(f"注册失败：{str(e)}")
            raise
        except Exception as e:
            print(f"注册用户异常（用户名：{username}）：{str(e)}")
            raise RuntimeError(f"注册失败：{str(e)}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """修改密码（修复逻辑+异常处理）"""
        try:
            user = User.get_by_id(user_id)
            if not user:
                raise ValueError("用户不存在")
            if not user.check_password(old_password):
                raise ValueError("原密码错误")

            # 新密码加密
            new_encrypted_pwd = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "UPDATE DEV.Dev_Users SET Password = ? WHERE User_ID = ?"
            cursor.execute(sql, (new_encrypted_pwd, user_id))
            conn.commit()
            return True
        except ValueError as e:
            print(f"修改密码失败：{str(e)}")
            raise
        except Exception as e:
            print(f"修改密码异常（用户ID：{user_id}）：{str(e)}")
            raise RuntimeError(f"修改密码失败：{str(e)}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def update_role(user_id, new_role):
        """更新用户角色（添加异常处理）"""
        if new_role not in ['管理员', '技术员']:
            raise ValueError("角色只能是'管理员'或'技术员'")

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "UPDATE DEV.Dev_Users SET Role = ? WHERE User_ID = ?"
            cursor.execute(sql, (new_role, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"更新角色失败（用户ID：{user_id}）：{str(e)}")
            raise RuntimeError(f"更新角色失败：{str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_all_by_role(role):
        """按角色查询用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            SELECT User_ID, Username, Password, Person_ID, Role, Create_Time, Last_Login, Status 
            FROM DEV.Dev_Users 
            WHERE Role = ?
            """
            cursor.execute(sql, (role,))
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(User(
                    user_id=row[0],
                    username=row[1],
                    password=row[2],
                    person_id=row[3],
                    role=row[4],
                    create_time=row[5],
                    last_login=row[6],
                    status=row[7]
                ))
            return users
        except Exception as e:
            print(f"按角色查询用户失败（角色：{role}）：{str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_by_id(user_id):
        """根据ID查询用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            SELECT User_ID, Username, Password, Person_ID, Role, Create_Time, Last_Login, Status 
            FROM DEV.Dev_Users 
            WHERE User_ID = ?
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                user_id=row[0],
                username=row[1],
                password=row[2],
                person_id=row[3],
                role=row[4],
                create_time=row[5],
                last_login=row[6],
                status=row[7]
            )
        except Exception as e:
            print(f"查询用户失败（ID：{user_id}）：{str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def update_last_login(user_id):
        """更新最后登录时间（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "UPDATE DEV.Dev_Users SET Last_Login = CURRENT_TIMESTAMP WHERE User_ID = ?"
            cursor.execute(sql, (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"更新最后登录时间失败（用户ID：{user_id}）：{str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_all():
        """获取所有用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            SELECT User_ID, Username, Password, Person_ID, Role, Create_Time, Last_Login, Status 
            FROM DEV.Dev_Users
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append(User(
                    user_id=row[0],
                    username=row[1],
                    password=row[2],
                    person_id=row[3],
                    role=row[4],
                    create_time=row[5],
                    last_login=row[6],
                    status=row[7]
                ))
            return users
        except Exception as e:
            print(f"获取所有用户失败：{str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def update_status(user_id, status):
        """更新用户状态（添加异常处理）"""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "UPDATE DEV.Dev_Users SET Status = ? WHERE User_ID = ?"
            cursor.execute(sql, (status, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"更新用户状态失败（用户ID：{user_id}）：{str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def add(username, password, person_id, role):
        """添加用户（添加异常处理）"""
        conn = None
        cursor = None
        try:
            # 密码加密（如果传入的是明文）
            if not password.startswith('0x') and len(password) != 64:  # 简单判断是否为SHA256加密值
                password = hashlib.sha256(password.encode('utf-8')).hexdigest()

            conn = get_db_connection()
            cursor = conn.cursor()
            sql = """
            INSERT INTO DEV.Dev_Users (Username, Password, Person_ID, Role, Create_Time) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            cursor.execute(sql, (username, password, person_id, role))
            conn.commit()
            return True
        except Exception as e:
            print(f"添加用户失败（用户名：{username}）：{str(e)}")
            raise RuntimeError(f"添加用户失败：{str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def delete_by_id(user_id):
        """通过用户ID删除用户"""
        # 1. 边界校验：用户ID必须大于0
        if user_id <= 0:
            print(f"删除用户失败：无效的用户ID {user_id}")
            return False

        conn = None
        cursor = None
        try:
            # 2. 建立数据库连接
            conn = get_db_connection()
            cursor = conn.cursor()

            # 3. 执行删除SQL
            delete_sql = "DELETE FROM DEV.Dev_Users WHERE User_ID = ?"
            cursor.execute(delete_sql, (user_id,))

            # 4. 提交事务
            conn.commit()
            # 5. 校验是否删除成功（影响行数>0表示删除成功）
            if cursor.rowcount > 0:
                print(f"用户ID {user_id} 删除成功，影响行数：{cursor.rowcount}")
                return True
            else:
                print(f"用户ID {user_id} 删除失败：未找到该用户")
                return False

        except Exception as e:
            # 数据库异常，回滚事务
            if conn:
                conn.rollback()
            print(f"删除用户失败：数据库错误 - {str(e)}")
            return False
        finally:
            # 6. 关闭游标和连接（无论成功失败都执行）
            if cursor:
                cursor.close()
            if conn:
                conn.close()