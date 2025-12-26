from utils.db import get_db_connection


class Staff:
    def __init__(self, id=None, name=None, mail_box=None, m_tel=None, per_pos=None):
        self.id = id
        self.name = name
        self.mail_box = mail_box
        self.m_tel = m_tel
        self.per_pos = per_pos  # 岗位（技术员/管理员，对应项目表0.1）

    def to_dict(self):
        """关联用户信息和负责设备信息（适配项目表0.1+表0.3）"""
        from models.user import User
        from models.equipment import Equipment
        user = User.get_by_person_id(self.id)
        responsible_equipments = Equipment.get_by_principal_id(self.id)
        return {
            'id': self.id,
            'name': self.name,
            'mail_box': self.mail_box,
            'm_tel': self.m_tel,
            'per_pos': self.per_pos,
            'user_info': user.to_dict() if user else {},
            'responsible_equipment_count': len(responsible_equipments),
            'responsible_equipments': [eq.to_dict() for eq in responsible_equipments]
        }

    @staticmethod
    def get_by_id(staff_id):
        """根据ID获取职工（核心查询）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person WHERE ID = ?"
            cursor.execute(sql, (staff_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Staff(
                id=row[0],
                name=row[1],
                mail_box=row[2],
                m_tel=row[3],
                per_pos=row[4]
            )
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all_by_position(position):
        """按岗位查询职工（适配项目表0.1的“岗位”筛选）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person WHERE Per_pos = ?"
            cursor.execute(sql, (position,))
            rows = cursor.fetchall()
            staffs = []
            for row in rows:
                staffs.append(Staff(
                    id=row[0],
                    name=row[1],
                    mail_box=row[2],
                    m_tel=row[3],
                    per_pos=row[4]
                ))
            return staffs
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add(name, mail_box, m_tel, per_pos):
        """新增职工（项目“人员管理”需求）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 校验手机号唯一（项目表0.1手机号唯一）
            if Staff.get_by_phone(m_tel):
                raise ValueError(f"手机号{m_tel}已被注册")
            sql = "INSERT INTO DEV.Dev_Person (Name, Mail_Box, M_Tel, Per_pos) VALUES (?, ?, ?, ?)"
            cursor.execute(sql, (name, mail_box, m_tel, per_pos))
            conn.commit()
            # 返回新增职工ID
            cursor.execute("SELECT MAX(ID) FROM DEV.Dev_Person")
            return cursor.fetchone()[0]
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all_staff():
        """获取所有人员列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person"
            cursor.execute(sql)
            rows = cursor.fetchall()
            staffs = []
            for row in rows:
                staffs.append(Staff(
                    id=row[0],
                    name=row[1],
                    mail_box=row[2],
                    m_tel=row[3],
                    per_pos=row[4]
                ))
            return staffs
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(staff_id, name=None, mail_box=None, m_tel=None, per_pos=None):
        """编辑职工信息（项目“人员管理”需求）"""
        staff = Staff.get_by_id(staff_id)
        if not staff:
            raise ValueError("职工不存在")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 动态构建更新SQL
            updates = []
            params = []
            if name:
                updates.append("Name = ?")
                params.append(name)
            if mail_box:
                updates.append("Mail_Box = ?")
                params.append(mail_box)
            if m_tel:
                # 校验手机号唯一
                existing = Staff.get_by_phone(m_tel)
                if existing and existing.id != staff_id:
                    raise ValueError(f"手机号{m_tel}已被注册")
                updates.append("M_Tel = ?")
                params.append(m_tel)
            if per_pos:
                updates.append("Per_pos = ?")
                params.append(per_pos)

            if not updates:
                raise ValueError("无需要更新的字段")

            sql = f"UPDATE DEV.Dev_Person SET {', '.join(updates)} WHERE ID = ?"
            params.append(staff_id)
            cursor.execute(sql, params)
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(staff_id):
        """删除职工（需先解除关联）"""
        # 校验是否关联用户
        from models.user import User
        if User.get_by_person_id(staff_id):
            raise ValueError("该职工已关联用户，需先删除用户")

        # 校验是否负责设备
        from models.equipment import Equipment
        if Equipment.get_by_principal_id(staff_id):
            raise ValueError("该职工负责设备，需先变更设备负责人")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM DEV.Dev_Person WHERE ID = ?"
            cursor.execute(sql, (staff_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_name(name):
        """根据姓名查询职工（项目表0.1姓名查询）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person WHERE Name = ?"
            cursor.execute(sql, (name,))
            row = cursor.fetchone()
            if not row:
                return None
            return Staff(
                id=row[0],
                name=row[1],
                mail_box=row[2],
                m_tel=row[3],
                per_pos=row[4]
            )
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_phone(m_tel):
        """根据手机号查询职工（项目表0.1手机号唯一校验）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person WHERE M_Tel = ?"
            cursor.execute(sql, (m_tel,))
            row = cursor.fetchone()
            if not row:
                return None
            return Staff(
                id=row[0],
                name=row[1],
                mail_box=row[2],
                m_tel=row[3],
                per_pos=row[4]
            )
        finally:
            cursor.close()
            conn.close()

    # 原有基础方法保留（get_all）
    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, Mail_Box, M_Tel, Per_pos FROM DEV.Dev_Person"
            cursor.execute(sql)
            rows = cursor.fetchall()
            staffs = []
            for row in rows:
                staffs.append(Staff(
                    id=row[0],
                    name=row[1],
                    mail_box=row[2],
                    m_tel=row[3],
                    per_pos=row[4]
                ))
            return staffs
        finally:
            cursor.close()
            conn.close()