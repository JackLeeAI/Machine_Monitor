from utils.db import get_db_connection
from datetime import datetime


class DataCollection:
    def __init__(self, id=None, mon_date=None, mon_id=None, mon_value=None, collector_id=None):
        self.id = id
        self.mon_date = mon_date  # 采集时间
        self.mon_id = mon_id  # 关联监测点ID
        self.mon_value = mon_value  # 采集值
        self.collector_id = collector_id  # 采集人ID

    def to_dict(self):
        """包含异常判定、关联信息"""
        from models.monitor_point import MonitorPoint
        from models.normal_range import NormalRange
        from models.staff import Staff

        point = MonitorPoint.get_by_id(self.mon_id)
        normal_range = NormalRange.get_by_monitor_id(self.mon_id)
        collector = Staff.get_by_id(self.collector_id)

        # 判定是否正常
        is_normal = True
        normal_range_str = ""
        if normal_range:
            normal_range_str = f"{float(normal_range.min_val)}-{float(normal_range.max_val)}{normal_range.note or ''}"
            is_normal = normal_range.min_val <= float(self.mon_value) <= normal_range.max_val

        return {
            'id': self.id,
            'mon_date': self.mon_date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.mon_date, 'strftime') and self.mon_date else '',
            'mon_id': self.mon_id,
            'mon_name': point.name if point else '',
            'mon_value': float(self.mon_value),
            'unit': point.unit if point else '',
            'collector_id': self.collector_id,
            'collector_name': collector.name if collector else '系统自动采集',
            'is_normal': is_normal,
            'normal_range': normal_range_str
        }

    @staticmethod
    def add(mon_id, mon_value, collector_id=None):
        """新增采集数据"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO DEV.Dev_Moni_Data (Mon_Date, Mon_ID, Mon_value, Collector_ID) VALUES (CURRENT_TIMESTAMP, ?, ?, ?)"
            cursor.execute(sql, (mon_id, mon_value, collector_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all(mon_id=None, start_time=None, end_time=None):
        """获取采集数据（支持筛选）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_Date, Mon_ID, Mon_value, Collector_ID FROM DEV.Dev_Moni_Data"
            params = []
            conditions = []

            if mon_id:
                conditions.append("Mon_ID = ?")
                params.append(mon_id)
            if start_time:
                conditions.append("Mon_Date >= ?")
                params.append(start_time)
            if end_time:
                conditions.append("Mon_Date <= ?")
                params.append(end_time)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY Mon_Date DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            collections = []
            for row in rows:
                collections.append(DataCollection(
                    id=row[0],
                    mon_date=row[1],
                    mon_id=row[2],
                    mon_value=row[3],
                    collector_id=row[4]
                ))
            return collections
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_latest_by_monitor_id(mon_id):
        """获取监测点最新采集数据"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_Date, Mon_ID, Mon_value, Collector_ID FROM DEV.Dev_Moni_Data WHERE Mon_ID = ? ORDER BY Mon_Date DESC LIMIT 1"
            cursor.execute(sql, (mon_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DataCollection(
                id=row[0],
                mon_date=row[1],
                mon_id=row[2],
                mon_value=row[3],
                collector_id=row[4]
            )
        finally:
            cursor.close()
            conn.close()