#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心跳测试命令行工具
用于测试设备心跳功能
"""

import argparse
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_heartbeat(equipment_id):
    """发送心跳请求"""
    try:
        logger.info(f"开始发送设备 {equipment_id} 的心跳")
        
        # 直接导入设备服务
        from services.equipment_service import EquipmentService
        
        # 调用心跳更新函数
        result = EquipmentService.update_equipment_heartbeat(equipment_id)
        
        if result:
            logger.info(f"设备 {equipment_id} 心跳发送成功")
            
            # 获取更新后的设备信息
            equipment = EquipmentService.get_equipment_by_id(equipment_id)
            if equipment:
                logger.info(f"设备 {equipment_id} 状态: {equipment.online_status}")
                logger.info(f"最后心跳时间: {equipment.last_heartbeat}")
            return True
        else:
            logger.error(f"设备 {equipment_id} 心跳发送失败")
            return False
            
    except Exception as e:
        logger.error(f"发送心跳过程中发生错误: {e}", exc_info=True)
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='设备心跳测试工具')
    parser.add_argument('equipment_id', type=int, help='设备ID')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 如果开启调试模式，设置日志级别为DEBUG
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # 发送心跳
    success = send_heartbeat(args.equipment_id)
    
    # 根据结果返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()