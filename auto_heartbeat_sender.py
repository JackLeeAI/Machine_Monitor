#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时给所有设备发送心跳包脚本
功能：定期获取所有设备ID并发送心跳，确保设备状态为在线
"""

import time
import schedule
from datetime import datetime
from services.equipment_service import EquipmentService
from utils.logger import logger

class AutoHeartbeatSender:
    def __init__(self, interval=10):
        """
        初始化自动心跳发送器
        :param interval: 发送间隔（秒），默认10秒
        """
        self.interval = interval
        self.total_heartbeats = 0
        self.success_count = 0
        
    def send_heartbeat_for_all_equipments(self):
        """为所有设备发送心跳包"""
        try:
            # 获取所有设备（不分页）
            equipments, total = EquipmentService.get_all_equipments(page=1, page_size=1000)
            
            if not equipments:
                logger.warning("未获取到任何设备信息")
                return
                
            logger.info(f"开始为{total}台设备发送心跳包...")
            
            success = 0
            failed = 0
            
            for equipment in equipments:
                try:
                    result = EquipmentService.update_equipment_heartbeat(equipment.id)
                    if result:
                        success += 1
                        logger.debug(f"设备{equipment.id}({equipment.name})心跳发送成功")
                    else:
                        failed += 1
                        logger.error(f"设备{equipment.id}({equipment.name})心跳发送失败")
                except Exception as e:
                    failed += 1
                    logger.error(f"设备{equipment.id}心跳发送异常: {str(e)}")
            
            self.total_heartbeats += total
            self.success_count += success
            
            logger.info(f"心跳包发送完成: 成功{success}台，失败{failed}台，总发送次数{self.total_heartbeats}，总成功率{self.success_count/self.total_heartbeats*100:.2f}%")
            
        except Exception as e:
            logger.error(f"发送心跳包时发生异常: {str(e)}")
    
    def start(self):
        """启动定时任务"""
        logger.info(f"自动心跳发送器已启动，发送间隔：{self.interval}秒")
        
        # 设置定时任务
        schedule.every(self.interval).seconds.do(self.send_heartbeat_for_all_equipments)
        
        # 立即执行一次
        self.send_heartbeat_for_all_equipments()
        
        # 循环执行
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("自动心跳发送器已停止")
                break
            except Exception as e:
                logger.error(f"定时任务执行异常: {str(e)}")
                time.sleep(1)

if __name__ == "__main__":
    # 创建并启动自动心跳发送器，默认每10秒发送一次
    heartbeat_sender = AutoHeartbeatSender(interval=10)
    heartbeat_sender.start()
