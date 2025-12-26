#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：直接测试设备心跳更新功能
"""

from models.equipment import Equipment
from datetime import datetime

# 测试设备ID列表（根据实际情况修改）
test_equipment_ids = [1, 2, 3, 4, 5]

print("开始测试设备心跳更新功能...")
print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for equipment_id in test_equipment_ids:
    try:
        result = Equipment.update_heartbeat(equipment_id)
        print(f"设备 {equipment_id}: 心跳更新 {'成功' if result else '失败'}")
        
        # 查询更新后的设备信息
        equipment = Equipment.get_by_id(equipment_id)
        if equipment:
            print(f"  设备名称: {equipment.name}")
            print(f"  在线状态: {equipment.online_status}")
            print(f"  最后心跳: {equipment.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if equipment.last_heartbeat else '无'}")
    except Exception as e:
        print(f"设备 {equipment_id}: 心跳更新失败 - {str(e)}")
    
    print()

print("测试完成！")
