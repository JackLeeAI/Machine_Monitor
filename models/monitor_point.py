from utils.db import get_db_connection


class MonitorPoint:
    def __init__(self, id=None, name=None, part_id=None, sense_type=None, sample_period=None,
                 sample_freq=None, sample_long=None, unit=None, admin_peron=None):
        self.id = id
        self.name = name
        self.part_id = part_id  # 关联部件ID
        self.sense_type = sense_type  # 关联传感类型ID
        self.sample_period = sample_period  # 采样周期（天）
        self.sample_freq = sample_freq  # 采样频率（次/天）
        self.sample_long = sample_long  # 采样时长（分钟）
        self.unit = unit  # 单位
        self.admin_peron = admin_peron  # 管理员ID

    def to_dict(self):
        """关联部件名称、传感类型名称、管理员名称"""
        from models.equipment_part import EquipmentPart
        from models.sensor_type import SensorType
        from models.staff import Staff
        part = EquipmentPart.get_by_id(self.part_id)
        sensor = SensorType.get_by_id(self.sense_type)
        admin = Staff.get_by_id(self.admin_peron)
        return {
            'id': self.id,
            'name': self.name,
            'part_id': self.part_id,
            'part_name': part.part_name if part else '',
            'sense_type': self.sense_type,
            'sense_name': sensor.name if sensor else '',
            'sample_period': self.sample_period,
            'sample_freq': self.sample_freq,
            'sample_long': self.sample_long,
            'unit': self.unit,
            'admin_peron': self.admin_peron,
            'admin_name': admin.name if admin else ''
        }

    @staticmethod
    def get_all(equipment_id=None, part_id=None):
        """获取所有监测点（支持筛选）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, PART_ID, Sense_Type, Sample_Period, Sample_Freq, Sample_Long, unit, Admin_Peron FROM DEV.Dev_Moni_Point"
            params = []

            if part_id:
                sql += " WHERE PART_ID = ?"
                params.append(part_id)
            elif equipment_id:
                # 根据设备ID查询关联的监测点（先查部件ID）
                from models.equipment_part import EquipmentPart
                parts, _ = EquipmentPart.get_all(equipment_id=equipment_id)
                part_ids = [p.id for p in parts]
                if part_ids:
                    placeholders = ', '.join(['?'] * len(part_ids))
                    sql += f" WHERE PART_ID IN ({placeholders})"
                    params.extend(part_ids)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            points = []
            for row in rows:
                # 确保ID不为空字符串
                point_id = row[0] if row[0] and str(row[0]).strip() else None
                points.append(MonitorPoint(
                    id=point_id,
                    name=row[1],
                    part_id=row[2],
                    sense_type=row[3],
                    sample_period=row[4],
                    sample_freq=row[5],
                    sample_long=row[6],
                    unit=row[7],
                    admin_peron=row[8]
                ))
            return points
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_part_id(part_id):
        """根据部件ID获取所有关联的监测点"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, PART_ID, Sense_Type, Sample_Period, Sample_Freq, Sample_Long, unit, Admin_Peron FROM DEV.Dev_Moni_Point WHERE PART_ID = ?"
            cursor.execute(sql, (part_id,))
            rows = cursor.fetchall()
            points = []
            for row in rows:
                point_id = row[0] if row[0] and str(row[0]).strip() else None
                points.append(MonitorPoint(
                    id=point_id,
                    name=row[1],
                    part_id=row[2],
                    sense_type=row[3],
                    sample_period=row[4],
                    sample_freq=row[5],
                    sample_long=row[6],
                    unit=row[7],
                    admin_peron=row[8]
                ))
            return points
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(point_id):
        """根据ID获取监测点"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Name, PART_ID, Sense_Type, Sample_Period, Sample_Freq, Sample_Long, unit, Admin_Peron FROM DEV.Dev_Moni_Point WHERE ID = ?"
            cursor.execute(sql, (point_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return MonitorPoint(
                id=row[0],
                name=row[1],
                part_id=row[2],
                sense_type=row[3],
                sample_period=row[4],
                sample_freq=row[5],
                sample_long=row[6],
                unit=row[7],
                admin_peron=row[8]
            )
        finally:
            cursor.close()
            conn.close()