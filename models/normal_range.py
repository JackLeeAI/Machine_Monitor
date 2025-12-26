from utils.db import get_db_connection  # 仅保留原生连接函数
# 移除：from utils.db import db

class NormalRange:
    def __init__(self, id=None, mon_id=None, min_val=None, max_val=None, note=None):
        self.id = id
        self.mon_id = mon_id  # 关联监测点ID（表0.6）
        self.min_val = min_val  # 最小值（表0.7）
        self.max_val = max_val  # 最大值（表0.7）
        self.note = note  # 备注（单位，表0.7）

    def to_dict(self):
        """关联监测点名称（表0.6+表0.7联动）"""
        from models.monitor_point import MonitorPoint
        point = MonitorPoint.get_by_id(self.mon_id)
        return {
            'id': self.id,
            'mon_id': self.mon_id,
            'mon_name': point.name if point else '',
            'min_val': float(self.min_val),
            'max_val': float(self.max_val),
            'note': self.note or ''
        }

    @staticmethod
    def get_by_monitor_id(mon_id):
        """根据监测点ID获取正常值范围（表0.7核心查询）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_ID, Min_Val, Max_Val, Note FROM DEV.Dev_Normal_Val WHERE Mon_ID = ?"
            cursor.execute(sql, (mon_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return NormalRange(
                id=row[0],
                mon_id=row[1],
                min_val=row[2],
                max_val=row[3],
                note=row[4]
            )
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all():
        """获取所有正常值范围（表0.7全量查询）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_ID, Min_Val, Max_Val, Note FROM DEV.Dev_Normal_Val"
            cursor.execute(sql)
            rows = cursor.fetchall()
            ranges = []
            for row in rows:
                ranges.append(NormalRange(
                    id=row[0],
                    mon_id=row[1],
                    min_val=row[2],
                    max_val=row[3],
                    note=row[4]
                ))
            return ranges
        finally:
            cursor.close()
            conn.close()