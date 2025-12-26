from datetime import datetime
from models.equipment import Equipment
from models.workshop import Workshop
from models.equipment_part import EquipmentPart
from utils.logger import logger
from config import HEARTBEAT_TIMEOUT
from werkzeug.exceptions import BadRequest
# 移除：from utils.db import db （已无db实例）

class EquipmentService:
    @staticmethod
    def get_all_equipments(workshop_id=None, use_state=None, page=1, page_size=10):
        """获取所有设备（支持筛选和分页）"""
        return Equipment.get_all(workshop_id=workshop_id, use_state=use_state, page=page, page_size=page_size)

    @staticmethod
    def get_equipment_by_id(equipment_id):
        """根据ID获取设备"""
        equipment = Equipment.get_by_id(equipment_id)
        if not equipment:
            raise BadRequest("设备不存在")
        return equipment

    @staticmethod
    def update_equipment_heartbeat(equipment_id):
        """更新设备心跳（标记在线）"""
        return Equipment.update_heartbeat(equipment_id)

    @staticmethod
    def check_equipment_online_status():
        """检查设备在线状态（超时标记离线）"""
        return Equipment.check_online_status()

    @staticmethod
    def get_equipment_parts(equipment_id):
        """获取设备的所有部件"""
        parts, _ = EquipmentPart.get_all(equipment_id=equipment_id)
        return parts

    @staticmethod
    def get_all_workshops():
        """获取所有车间"""
        return Workshop.get_all()