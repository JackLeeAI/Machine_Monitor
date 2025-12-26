# services/data_service.py
from utils.db import get_db_connection
from models.monitor_point import MonitorPoint  # 需确保模型类字段与新表匹配
from utils.db import logger
from datetime import datetime,date,time

class DataService:
    @staticmethod
    def get_all_monitor_points(part_id=None, sense_type=None):
        """
        查询所有监控点（支持按部件ID/传感器类型筛选）
        :param part_id: 部件ID（PART_ID），None则不筛选
        :param sense_type: 传感器类型ID（Sense_Type），None则不筛选
        :return: MonitorPoint对象列表
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        monitor_points = []

        try:
            # 适配实际的Dev_Moni_Point表结构
            sql = """
                SELECT ID, Name, PART_ID, Sense_Type, Sample_Period, 
                       Sample_Freq, Sample_Long, unit, Admin_Peron
                FROM DEV.Dev_Moni_Point
            """
            params = []
            conditions = []

            # 按部件ID筛选（原表关联Dev_Part的外键）
            if part_id:
                conditions.append("PART_ID = ?")
                params.append(part_id)

            # 按传感器类型筛选
            if sense_type:
                conditions.append("Sense_Type = ?")
                params.append(sense_type)

            # 拼接筛选条件
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            # 执行查询
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # 封装为MonitorPoint对象（匹配新表字段）
            for row in rows:
                point = MonitorPoint()
                point.id = row[0]  # 监控点ID
                point.name = row[1]  # 监控点名称（原Name）
                point.part_id = row[2]  # 关联部件ID（PART_ID）
                point.sense_type = row[3]  # 传感器类型ID（Sense_Type）
                point.sample_period = row[4]  # 采样周期
                point.sample_freq = row[5]  # 采样频率
                point.sample_long = row[6]  # 采样时长
                point.unit = row[7]  # 单位（原unit）
                point.admin_person = row[8]  # 负责人ID（Admin_Peron）
                monitor_points.append(point)

            return monitor_points
        except Exception as e:
            print(f"查询监控点失败：{str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    # @staticmethod
    # def get_history_data(start_date=None, end_date=None, part_id=None, sense_type=None):
    #     """
    #     查询设备历史采集数据（适配新的监控点表关联关系）
    #     :param start_date: 开始时间
    #     :param end_date: 结束时间
    #     :param part_id: 部件ID（筛选该部件下的所有监控点数据）
    #     :param sense_type: 传感器类型ID（筛选该类型的监控点数据）
    #     :return: 历史数据列表
    #     """
    #     conn = get_db_connection()
    #     cursor = conn.cursor()
    #     history_data = []
    #     try:
    #         # 关联监控点表查询（适配新的Dev_Moni_Point结构）
    #         sql = """
    #             SELECT dc.ID, dc.Point_ID, dc.Collect_Time, dc.Value, mp.Name, mp.unit
    #             FROM DEV.Dev_Data_Collection dc
    #             LEFT JOIN DEV.Dev_Moni_Point mp ON dc.Point_ID = mp.ID
    #         """
    #         params = []
    #         conditions = []
    #
    #         # 基础时间筛选
    #         if start_date:
    #             conditions.append("dc.Collect_Time >= ?")
    #             params.append(start_date)
    #         if end_date:
    #             conditions.append("dc.Collect_Time <= ?")
    #             params.append(end_date)
    #
    #         # 按部件ID筛选（关联监控点表的PART_ID）
    #         if part_id:
    #             conditions.append("mp.PART_ID = ?")
    #             params.append(part_id)
    #
    #         # 按传感器类型筛选
    #         if sense_type:
    #             conditions.append("mp.Sense_Type = ?")
    #             params.append(sense_type)
    #
    #         # 拼接筛选条件
    #         if conditions:
    #             sql += " WHERE " + " AND ".join(conditions)
    #
    #         # 按采集时间排序
    #         sql += " ORDER BY dc.Collect_Time DESC"
    #
    #         cursor.execute(sql, params)
    #         rows = cursor.fetchall()
    #
    #         # 封装历史数据（包含监控点名称和单位，更实用）
    #         for row in rows:
    #             history_data.append({
    #                 'id': row[0],  # 采集记录ID
    #                 'point_id': row[1],  # 监控点ID
    #                 'collect_time': row[2],  # 采集时间
    #                 'value': row[3],  # 采集值
    #                 'point_name': row[4],  # 监控点名称
    #                 'unit': row[5]  # 单位
    #             })
    #         return history_data
    #     except Exception as e:
    #         print(f"查询历史数据失败：{str(e)}")
    #         return []
    #     finally:
    #         cursor.close()
    #         conn.close()

    @staticmethod
    def get_latest_data_by_monitor_point(point_id):
        """
        获取单个监测点的最新采集数据（适配 Dev_Moni_Data 表结构）
        :param point_id: 监测点ID（Dev_Moni_Point表的主键）
        :return: DataItem对象/None - 包含最新采集数据，无数据返回None
        """
        # 参数校验：避免无效查询
        if not point_id or not isinstance(point_id, (int, str)):
            print(f"监测点ID参数无效：{point_id}（需为整数/字符串类型）")
            return None
        # 检查是否为空字符串
        if isinstance(point_id, str) and point_id.strip() == '':
            print(f"监测点ID参数无效：空字符串")
            return None

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 核心SQL：适配 Dev_Moni_Data 表的字段名
            sql = """
                SELECT ID, Mon_ID, Mon_Date, Mon_value, Collector_ID 
                FROM DEV.Dev_Moni_Data
                WHERE Mon_ID = ?  -- Mon_ID 关联监测点表的ID
                ORDER BY Mon_Date DESC  -- 按采集时间降序
                LIMIT 1  -- 只取最新一条
            """
            cursor.execute(sql, [point_id])
            row = cursor.fetchone()

            # 无数据时返回None
            if not row:
                print(f"监测点{point_id}暂无采集数据")
                return None

            # 封装为数据对象（保持to_dict方法，适配原有调用逻辑）
            class DataItem:
                def __init__(self, id, mon_id, mon_date, mon_value, collector_id):
                    self.id = id  # 采集记录ID
                    self.point_id = mon_id  # 兼容原有代码的point_id字段名
                    self.collect_time = mon_date  # 兼容原有代码的collect_time字段名
                    self.value = mon_value  # 兼容原有代码的value字段名
                    self.collector_id = collector_id  # 新增：采集人ID

                def to_dict(self):
                    """转换为字典，保持原有字段名兼容前端/模板"""
                    return {
                        'id': self.id,
                        'point_id': self.point_id,  # 仍用point_id，避免调用方修改
                        'collect_time': self.collect_time,  # 仍用collect_time，兼容原有逻辑
                        'value': self.value,  # 仍用value，兼容原有逻辑
                        'collector_id': self.collector_id  # 新增字段：采集人ID
                    }

            # 映射表字段到对象（注意row的索引顺序和SQL查询字段一致）
            return DataItem(
                id=row[0],
                mon_id=row[1],
                mon_date=row[2],
                mon_value=row[3],
                collector_id=row[4]
            )
        except Exception as e:
            print(f"获取监测点{point_id}最新数据失败：{str(e)}")
            return None
        finally:
            # 安全释放数据库资源（无论成功/失败都执行）
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass

    @staticmethod
    def get_monitor_points_by_equipment_id(equipment_id):
        """
        通过设备ID查询该设备下所有关联的监测点
        核心逻辑：设备ID → 部件表(Dev_Part) → 监测点表(Dev_Moni_Point)
        :param equipment_id: 主设备ID（Dev_Equipment表的主键）
        :return: list[MonitorPoint] - 监测点对象列表，查询失败/无数据返回空列表
        """
        # 1. 参数校验（避免无效查询）
        if not equipment_id or not isinstance(equipment_id, (int, str)):
            print(f"设备ID参数无效：{equipment_id}（需为整数/字符串类型）")
            return []

        conn = None
        cursor = None
        monitor_points = []

        try:
            # 2. 获取数据库连接
            conn = get_db_connection()
            cursor = conn.cursor()

            # 3. 核心SQL：关联部件表查询设备下的所有监测点
            # 注意：Dev_Part表的MID字段与设备关联
            sql = """
                    SELECT 
                        mp.ID,          -- 监测点ID
                        mp.Name,        -- 监测点名称
                        mp.PART_ID,     -- 关联部件ID
                        mp.Sense_Type,  -- 传感器类型ID
                        mp.Sample_Period, -- 采样周期
                        mp.Sample_Freq,   -- 采样频率
                        mp.Sample_Long,   -- 采样时长
                        mp.unit,        -- 单位
                        mp.Admin_Peron  -- 负责人ID
                    FROM DEV.Dev_Moni_Point mp
                    LEFT JOIN DEV.Dev_Part p ON mp.PART_ID = p.ID
                    WHERE p.MID = ?  -- 通过部件表的MID关联主设备
                    ORDER BY mp.ID ASC  -- 按监测点ID排序，结果更规整
                """

            # 4. 执行查询（参数化查询，防止SQL注入）
            cursor.execute(sql, [equipment_id])
            rows = cursor.fetchall()

            # 5. 封装为MonitorPoint对象
            for row in rows:
                point = MonitorPoint()
                point.id = row[0]  # 监测点ID
                point.name = row[1]  # 监测点名称
                point.part_id = row[2]  # 关联部件ID
                point.sense_type = row[3]  # 传感器类型ID
                point.sample_period = row[4]  # 采样周期
                point.sample_freq = row[5]  # 采样频率
                point.sample_long = row[6]  # 采样时长
                point.unit = row[7]  # 单位
                point.admin_peron = row[8]  # 负责人ID（注意字段名是admin_peron）
                monitor_points.append(point)

            print(f"设备{equipment_id}查询到{len(monitor_points)}个监测点")
            return monitor_points

        except Exception as e:
            # 6. 异常捕获（详细日志便于排查问题）
            print(f"按设备ID查询监测点失败：设备ID={equipment_id}，错误信息={str(e)}")
            return []

        finally:
            # 7. 资源释放（无论成功/失败，确保关闭游标和连接）
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass

    @staticmethod
    def get_history_data(start_date, end_date, mon_id):
        """
        修复元组解析错误：适配游标返回元组的情况
        """
        # 1. 参数校验与预处理
        start_dt = None
        end_dt = None
        try:
            if start_date and start_date.strip():
                start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
                start_dt = start_dt.replace(hour=0, minute=0, second=0)
            if end_date and end_date.strip():
                end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError as e:
            logger.error(f"日期格式错误：{str(e)} | start={start_date} | end={end_date}")
            return []

        # 2. 数据库查询（元组格式适配）
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()  # 普通游标，返回元组

            # 核心SQL（保持不变）
            sql = """
                SELECT 
                    d.ID AS data_id,
                    d.Mon_Date AS mon_date,
                    mp.Name AS mon_name,
                    st.name AS sense_name,
                    d.Mon_value AS mon_value,
                    mp.unit AS unit,
                    CONCAT(nv.Min_Val, '-', nv.Max_Val) AS normal_range,
                    nv.Min_Val AS min_val,
                    nv.Max_Val AS max_val,
                    p.Name AS collector_name
                FROM DEV.Dev_Moni_Data d
                LEFT JOIN DEV.Dev_Moni_Point mp ON d.Mon_ID = mp.ID
                LEFT JOIN DEV.Dev_Sense_Type st ON mp.Sense_Type = st.ID
                LEFT JOIN DEV.Dev_Normal_Val nv ON d.Mon_ID = nv.Mon_ID
                LEFT JOIN DEV.Dev_Person p ON d.Collector_ID = p.ID
                WHERE 1=1
            """
            params = []

            # 添加时间/监测点条件
            if start_dt:
                sql += " AND d.Mon_Date >= ?"
                params.append(start_dt)
            if end_dt:
                sql += " AND d.Mon_Date <= ?"
                params.append(end_dt)
            if mon_id and mon_id.strip() != "":
                sql += " AND d.Mon_ID = ?"
                params.append(mon_id.strip())

            sql += " ORDER BY d.Mon_Date DESC"
            logger.info(f"执行查询SQL：{sql} | 参数：{params}")
            cursor.execute(sql, params)
            rows = cursor.fetchall()  # 返回元组列表

            # 3. 格式化结果（适配元组格式，按字段顺序取值）
            history_data = []
            for row in rows:
                # === 关键修复：按SQL查询的字段顺序解析元组 ===
                # row索引对应SQL的SELECT顺序：
                # 0:data_id, 1:mon_date, 2:mon_name, 3:sense_name, 4:mon_value,
                # 5:unit, 6:normal_range, 7:min_val, 8:max_val, 9:collector_name

                # 处理采集时间
                mon_date_str = ""
                if row[1]:  # row[1] 对应 mon_date
                    try:
                        if isinstance(row[1], datetime):
                            mon_date_str = row[1].strftime("%Y-%m-%d %H:%M:%S")
                        elif isinstance(row[1], str):
                            mon_date_str = row[1][:19]
                    except:
                        mon_date_str = str(row[1])[:20]

                # 判断是否正常
                is_normal = True
                mon_value = row[4]
                min_val = row[7]
                max_val = row[8]
                if mon_value is not None and min_val is not None and max_val is not None:
                    try:
                        mon_value_num = float(mon_value)
                        min_val_num = float(min_val)
                        max_val_num = float(max_val)
                        is_normal = min_val_num <= mon_value_num <= max_val_num
                    except:
                        is_normal = False

                # 组装数据（元组索引取值）
                history_data.append({
                    "mon_date": mon_date_str,
                    "mon_name": row[2].strip() if row[2] else "未知监测点",
                    "sense_name": row[3].strip() if row[3] else "未知传感类型",
                    "mon_value": row[4] or "",
                    "unit": row[5].strip() if row[5] else "",
                    "normal_range": row[6].strip() if row[6] else "未配置正常范围",
                    "is_normal": is_normal,
                    "collector_name": row[9].strip() if row[9] else "未知采集人"
                })

            logger.info(f"查询完成：共{len(history_data)}条数据")
            return history_data

        except Exception as e:
            logger.error(f"查询失败：{str(e)}", exc_info=True)
            return []
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            try:
                if conn:
                    conn.close()
            except:
                pass