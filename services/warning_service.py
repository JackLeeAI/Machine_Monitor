# services/warning_service.py
from utils.db import get_db_connection
from models.early_warning import EarlyWarning  # 保留模型类，用于数据封装


class WarningService:
    @staticmethod
    def get_all_warnings(msg_state=None, start_time=None, end_time=None):
        """
        获取所有预警信息（适配原生SQL，匹配实际表 DEV.Dev_Warning）
        :param msg_state: 预警状态（待处理/已处理），None则查询所有
        :param start_time: 开始时间，None则不限制
        :param end_time: 结束时间，None则不限制
        :return: EarlyWarning对象列表
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        warnings = []

        try:
            # 构建基础SQL查询
            sql = "SELECT ID, Mon_ID, Msg_Text, Per_ID, Msg_State, Happen_Time, Handle_Time FROM DEV.DEV_WARNING"
            params = []
            conditions = []

            # 条件过滤
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

            # 拼接条件和排序
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY Happen_Time DESC"

            # 执行查询
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # 封装为EarlyWarning对象
            for row in rows:
                warning = EarlyWarning(
                    id=row[0],
                    mon_id=row[1],
                    msg_text=row[2],
                    per_id=row[3],
                    msg_state=row[4],
                    happen_time=row[5],
                    handle_time=row[6]
                )
                warnings.append(warning)

            return warnings
        except Exception as e:
            print(f"查询预警失败：{str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    # 可选：补充其他预警相关方法（如更新状态、删除预警）
    @staticmethod
    def update_warning_state(warning_id, new_state, handle_remark=None, handler_id=None, handle_time=None):
        """
        更新预警状态（待处理→已处理），同时可选更新处理时间、处理人、备注
        :param warning_id: 预警ID
        :param new_state: 新状态（已处理/处理中/待处理）
        :param handle_remark: 处理备注（可选）
        :param handler_id: 处理人ID（可选）
        :param handle_time: 处理时间（可选，如 datetime.datetime.now()）
        :return: 布尔值，更新是否成功
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 先获取原预警内容
            cursor.execute("SELECT Msg_Text FROM DEV.DEV_WARNING WHERE ID = ?", (warning_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            msg_text = row[0]
    
            # 如果有处理备注，追加到预警内容中
            if handle_remark:
                # 检查并截断字符串，确保不超过CHAR(50)的长度限制
                new_content = f"{msg_text} | 处理备注：{handle_remark}"
                # CHAR(50)类型最多存储50个字符，需要截断
                msg_text = new_content[:50]
            
            # 构建SQL语句和参数
            sql_parts = ["UPDATE DEV.DEV_WARNING SET Msg_State = ?, Msg_Text = ?"]
            params = [new_state, msg_text]
           
            # 添加处理人ID
            if handler_id:
                sql_parts.append("Per_ID = ?")
                params.append(handler_id)
            
            # 添加处理时间
            if handle_time:
                sql_parts.append("Handle_Time = ?")
                params.append(handle_time)
            else:
                # 如果没有提供处理时间，使用数据库当前时间
                sql_parts.append("Handle_Time = CURRENT_TIMESTAMP")
            
            # 组合SET部分
            sql = ", ".join(sql_parts)
            
            # 添加WHERE子句
            sql += " WHERE ID = ?"
            params.append(warning_id)
    
            # 执行更新
            cursor.execute(sql, params)
            conn.commit()
         
            return cursor.rowcount > 0
        except Exception as e:
            print(f"更新预警状态失败：{str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()