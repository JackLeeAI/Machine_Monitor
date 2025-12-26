from utils.db import get_db_connection  # 仅保留连接函数，删除db导入


class EquipmentPart:
    def __init__(self, id=None, mid=None, part_name=None, description=None):
        self.id = id
        self.mid = mid  # 关联主设备ID（Dev_Part表的MID字段）
        self.part_name = part_name
        self.description = description

    def to_dict(self):
        """转换为字典（关联设备名称和监测点，增强数据可读性）"""
        from models.equipment import Equipment
        from models.monitor_point import MonitorPoint
        equipment = None
        monitor_points = []
        try:
            # 避免设备查询失败导致整体报错
            equipment = Equipment.get_by_id(self.mid)
        except Exception as e:
            print(f"查询部件{self.id}关联设备失败：{str(e)}")
        
        try:
            # 查询部件关联的监测点
            monitor_points = MonitorPoint.get_all(part_id=self.id)
        except Exception as e:
            print(f"查询部件{self.id}关联监测点失败：{str(e)}")

        return {
            'ID': self.id,
            'mid': self.mid,
            'equipment_name': equipment.name if equipment else '未知设备',
            'Part_Name': self.part_name or '',
            'Description': self.description or '无',
            'monitor_points': monitor_points
        }

    @staticmethod
    def get_all(equipment_id=None, page=None, page_size=None):
        """
        查询所有设备部件（支持按主设备ID筛选和分页）
        :param equipment_id: 主设备ID（MID），None则查询所有
        :param page: 页码，None则不分页
        :param page_size: 每页数量，None则不分页
        :return: tuple(list[EquipmentPart], int) - 部件对象列表和总数量
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 先查询总数量
            count_sql = "SELECT COUNT(*) FROM DEV.Dev_Part"
            count_params = []
            if equipment_id:
                count_sql += " WHERE MID = ?"
                count_params.append(equipment_id)
            cursor.execute(count_sql, count_params)
            total_count = cursor.fetchone()[0]

            # 查询数据
            sql = "SELECT ID, MID, Part_Name, Description FROM DEV.Dev_Part"
            params = []
            if equipment_id:
                sql += " WHERE MID = ?"
                params.append(equipment_id)

            # 添加分页
            if page and page_size:
                offset = (page - 1) * page_size
                sql += " LIMIT ? OFFSET ?"
                params.extend([page_size, offset])

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            parts = []
            for row in rows:
                # 确保ID不为空字符串
                part_id = row[0] if row[0] and str(row[0]).strip() else None
                parts.append(EquipmentPart(
                    id=part_id,
                    mid=row[1],
                    part_name=row[2],
                    description=row[3]
                ))
            return parts, total_count
        except Exception as e:
            print(f"查询设备部件失败：{str(e)}")
            return [], 0
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(part_id):
        """
        通过部件ID查询单个部件信息
        :param part_id: 部件ID（Dev_Part表主键）
        :return: EquipmentPart对象/None
        """
        # 参数校验
        if not part_id or not isinstance(part_id, (int, str)):
            print(f"部件ID参数无效：{part_id}")
            return None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, MID, Part_Name, Description FROM DEV.Dev_Part WHERE ID = ?"
            cursor.execute(sql, [part_id])
            row = cursor.fetchone()

            if not row:
                print(f"未查询到ID={part_id}的设备部件")
                return None

            return EquipmentPart(
                id=row[0],
                mid=row[1],
                part_name=row[2],
                description=row[3]
            )
        except Exception as e:
            print(f"查询部件{part_id}失败：{str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def add(self):
        """
        新增设备部件（调用对象的实例方法，需先初始化属性）
        :return: bool - 新增成功返回True，失败返回False
        """
        # 参数校验（必填字段）
        if not self.mid or not self.part_name:
            print("新增部件失败：主设备ID（mid）和部件名称（part_name）为必填项")
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 假设ID为自增主键（若不是，需传入ID）
            sql = """
                INSERT INTO DEV.Dev_Part (MID, Part_Name, Description)
                VALUES (?, ?, ?)
            """
            cursor.execute(sql, [self.mid, self.part_name, self.description or ''])
            conn.commit()  # 提交事务
            # 获取自增ID（若需要）
            self.id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            print(f"新增部件成功：ID={self.id}，名称={self.part_name}")
            return True
        except Exception as e:
            conn.rollback()  # 异常回滚
            print(f"新增部件失败：{str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update(self):
        """
        更新设备部件（调用对象的实例方法，需先通过get_by_id获取对象并修改属性）
        :return: bool - 更新成功返回True，失败返回False
        """
        # 参数校验
        if not self.id:
            print("更新部件失败：部件ID（id）为必填项")
            return False
        if not self.mid or not self.part_name:
            print("更新部件失败：主设备ID（mid）和部件名称（part_name）为必填项")
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
                UPDATE DEV.Dev_Part
                SET MID = ?, Part_Name = ?, Description = ?
                WHERE ID = ?
            """
            cursor.execute(sql, [self.mid, self.part_name, self.description or '', self.id])
            conn.commit()

            # 检查是否有数据被更新
            if cursor.rowcount == 0:
                print(f"更新部件失败：未找到ID={self.id}的部件或数据无变化")
                return False

            print(f"更新部件成功：ID={self.id}")
            return True
        except Exception as e:
            conn.rollback()
            print(f"更新部件{self.id}失败：{str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(part_id):
        """
        删除设备部件（静态方法，直接传入ID）
        :param part_id: 部件ID
        :return: bool - 删除成功返回True，失败返回False
        """
        # 参数校验
        if not part_id or not isinstance(part_id, (int, str)):
            print(f"删除部件失败：无效的部件ID {part_id}")
            return False

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 先检查是否有关联的监测点（可选：避免外键约束报错）
            check_sql = "SELECT COUNT(*) FROM DEV.Dev_Moni_Point WHERE PART_ID = ?"
            cursor.execute(check_sql, [part_id])
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"删除部件{part_id}失败：该部件关联{count}个监测点，无法直接删除")
                return False

            # 执行删除
            sql = "DELETE FROM DEV.Dev_Part WHERE ID = ?"
            cursor.execute(sql, [part_id])
            conn.commit()

            if cursor.rowcount == 0:
                print(f"删除部件失败：未找到ID={part_id}的部件")
                return False

            print(f"删除部件成功：ID={part_id}")
            return True
        except Exception as e:
            conn.rollback()
            print(f"删除部件{part_id}失败：{str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    # 新增：按设备ID查询部件（适配之前的equipment_detail函数）
    @staticmethod
    def get_equipment_parts(eq_id):
        """
        快捷方法：查询指定设备下的所有部件（兼容EquipmentService的调用）
        :param eq_id: 设备ID（MID）
        :return: list[EquipmentPart]
        """
        parts, _ = EquipmentPart.get_all(equipment_id=eq_id)
        return parts

    @staticmethod
    def count_all():
        """获取部件总数"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT COUNT(*) FROM DEV.Dev_Part"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"统计部件总数失败：{str(e)}")
            return 0
        finally:
            cursor.close()
            conn.close()