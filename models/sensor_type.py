from utils.db import get_db_connection

class SensorType:
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
        """获取所有传感类型"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, name FROM DEV.Dev_Sense_Type"
            cursor.execute(sql)
            rows = cursor.fetchall()
            types = []
            for row in rows:
                types.append(SensorType(
                    id=row[0],
                    name=row[1]
                ))
            return types
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(type_id):
        """根据ID获取传感类型"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, name FROM DEV.Dev_Sense_Type WHERE ID = ?"
            cursor.execute(sql, (type_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return SensorType(
                id=row[0],
                name=row[1]
            )
        finally:
            cursor.close()
            conn.close()