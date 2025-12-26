from utils.db import get_db_connection
from datetime import datetime


class EarlyWarning:
    def __init__(self, id=None, mon_id=None, msg_text=None, per_id=None, msg_state=None, happen_time=None,
                 handle_time=None):
        self.id = id
        self.mon_id = mon_id  # 关联监测点ID
        self.msg_text = msg_text  # 预警内容
        self.per_id = per_id  # 处理人ID
        self.msg_state = msg_state  # 处理状态：待处理/处理中/已处理
        self.happen_time = happen_time  # 发生时间
        self.handle_time = handle_time  # 处理时间

    def to_dict(self):
        """关联监测点名称、处理人名称"""
        from models.monitor_point import MonitorPoint
        from models.staff import Staff

        point = MonitorPoint.get_by_id(self.mon_id)
        handler = Staff.get_by_id(self.per_id)

        return {
            'id': self.id,
            'mon_id': self.mon_id,
            'mon_name': point.name if point else '',
            'msg_text': self.msg_text,
            'per_id': self.per_id,
            'handler_name': handler.name if handler else '未分配',
            'msg_state': self.msg_state.strip() if self.msg_state else '待处理',
            'happen_time': self.happen_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.happen_time, 'strftime') and self.happen_time else '',
            'handle_time': self.handle_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.handle_time, 'strftime') and self.handle_time else '未处理'
        }

    @staticmethod
    def add(mon_id, msg_text):
        """新增预警"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO DEV.DEV_WARNING (Mon_ID, Msg_Text, Msg_State, Happen_Time) VALUES (?, ?, '待处理', CURRENT_TIMESTAMP)"
            cursor.execute(sql, (mon_id, msg_text))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all(msg_state=None, start_time=None, end_time=None):
        """获取所有预警（支持筛选）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_ID, Msg_Text, Per_ID, Msg_State, Happen_Time, Handle_Time FROM DEV.DEV_WARNING"
            params = []
            conditions = []

            if msg_state:
                conditions.append("Msg_State = ?")
                params.append(msg_state)
            if start_time:
                conditions.append("Happen_Time >= ?")
                params.append(start_time)
            if end_time:
                conditions.append("Happen_Time <= ?")
                params.append(end_time)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY Happen_Time DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            warnings = []
            for row in rows:
                warnings.append(EarlyWarning(
                    id=row[0],
                    mon_id=row[1],
                    msg_text=row[2],
                    per_id=row[3],
                    msg_state=row[4],
                    happen_time=row[5],
                    handle_time=row[6]
                ))
            return warnings
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(warn_id):
        """根据ID获取预警"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Mon_ID, Msg_Text, Per_ID, Msg_State, Happen_Time, Handle_Time FROM DEV.DEV_WARNING WHERE ID = ?"
            cursor.execute(sql, (warn_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return EarlyWarning(
                id=row[0],
                mon_id=row[1],
                msg_text=row[2],
                per_id=row[3],
                msg_state=row[4],
                happen_time=row[5],
                handle_time=row[6]
            )
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def handle(warn_id, handler_id, handle_note, handle_state):
        """处理预警"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 更新预警内容（追加处理备注）
            warning = EarlyWarning.get_by_id(warn_id)
            new_msg_text = f"{warning.msg_text} | 处理备注：{handle_note}"

            sql = "UPDATE DEV.DEV_WARNING SET Per_ID = ?, Msg_State = ?, Handle_Time = CURRENT_TIMESTAMP, Msg_Text = ? WHERE ID = ?"
            cursor.execute(sql, (handler_id, handle_state, new_msg_text, warn_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(warn_id):
        """删除预警（仅管理员）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM DEV.DEV_WARNING WHERE ID = ?"
            cursor.execute(sql, (warn_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()