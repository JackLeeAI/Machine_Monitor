import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 直接测试心跳处理逻辑
def test_heartbeat_logic():
    """直接测试心跳处理逻辑"""
    try:
        logger.info("开始测试心跳处理逻辑")
        
        # 直接导入设备服务
        from services.equipment_service import EquipmentService
        
        # 测试设备ID
        test_equipment_id = 1
        
        # 调用心跳更新函数
        logger.info(f"更新设备 {test_equipment_id} 的心跳")
        result = EquipmentService.update_equipment_heartbeat(test_equipment_id)
        logger.info(f"心跳更新结果: {result}")
        
        # 检查设备在线状态
        logger.info(f"检查设备 {test_equipment_id} 的在线状态")
        from services.equipment_service import Equipment
        equipment = EquipmentService.get_equipment_by_id(test_equipment_id)
        if equipment:
            logger.info(f"设备 {test_equipment_id} 的状态: 在线状态={equipment.online_status}, 最后心跳={equipment.last_heartbeat}")
        else:
            logger.error(f"未找到设备 {test_equipment_id}")
        
        logger.info("心跳处理逻辑测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    test_heartbeat_logic()