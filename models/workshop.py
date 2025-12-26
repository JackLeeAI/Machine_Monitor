from utils.db import get_db_connection

class Workshop:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

    @staticmethod
    def get_all():
        """获取所有车间"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, name FROM DEV.Dev_Place"
            cursor.execute(sql)
            rows = cursor.fetchall()
            workshops = []
            for row in rows:
                workshops.append(Workshop(
                    id=row[0],
                    name=row[1]
                ))
            return workshops
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_name(workshop_name):
        """
        通过车间名称查询车间信息
        :param workshop_name: 车间名称（字符串）
        :return: Workshop实例（存在）/ None（不存在/查询失败）
        """
        # 1. 边界校验：车间名称不能为空
        if not workshop_name or workshop_name.strip() == '':
            print("查询车间失败：车间名称不能为空")
            return None

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 3. 执行查询SQL（模糊查询/精准查询可选）
            sql = "SELECT * FROM DEV.Dev_Place WHERE Name = ?"
            cursor.execute(sql, (workshop_name.strip(),))
            result = cursor.fetchone()

            # 6. 结果转换：存在则返回Workshop实例，否则返回None
            if result:
                return Workshop(
                    id=result[0],
                    name=result[1],
                )
            return None

        except Exception as e:
            # 其他未知异常
            print(f"查询车间失败：未知错误 - {str(e)}")
            return None
        finally:
            # 7. 关闭游标和连接，释放资源
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    @staticmethod
    def get_by_id(workshop_id):
        """根据ID获取车间"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, name FROM DEV.Dev_Place WHERE ID = ?"
            cursor.execute(sql, (workshop_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Workshop(
                id=row[0],
                name=row[1]
            )
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add(workshop_name):
        """新增车间"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 查询最大ID
            cursor.execute("SELECT MAX(ID) FROM DEV.Dev_Place")
            max_id = cursor.fetchone()[0]
            new_id = max_id + 1 if max_id is not None else 1
            
            # 插入新车间
            sql = "INSERT INTO DEV.Dev_Place (ID, name) VALUES (?, ?)"
            cursor.execute(sql, (new_id, workshop_name))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(workshop_id, new_name):
        """编辑车间名称"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "UPDATE DEV.Dev_Place SET name = ? WHERE ID = ?"
            cursor.execute(sql, (new_name, workshop_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(workshop_id):
        """删除车间"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM DEV.Dev_Place WHERE ID = ?"
            cursor.execute(sql, (workshop_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()