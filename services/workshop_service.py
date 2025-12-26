# services/workshop_service.py
from utils.db import get_db_connection
from models.workshop import Workshop

class WorkshopService:
    @staticmethod
    def get_all_workshops():
        """查询所有车间信息（适配达梦数据库）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        workshops = []

        try:
            # 注意：表名/字段名需匹配你的实际数据库结构
            # 若表名为 DEV.Dev_Workshop，字段为 ID/Name/Address/Manager
            cursor.execute("""
                SELECT ID, Name
                FROM DEV.DEV_PLACE 
                ORDER BY ID
            """)
            rows = cursor.fetchall()

            for row in rows:
                workshop = Workshop()
                workshop.id = row[0]
                workshop.name = row[1]
                workshops.append(workshop)

            return workshops
        except Exception as e:
            print(f"查询车间失败：{str(e)}")
            return []  # 失败时返回空列表，避免模板报错
        finally:
            cursor.close()
            conn.close()