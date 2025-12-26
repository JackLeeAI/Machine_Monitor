from utils.db import get_db_connection
from datetime import datetime


class Equipment:
    def __init__(self, id=None, equip_code=None, name=None, pos_id=None, person_id=None, pur_date=None, first_time=None,
                 use_state=None, online_status='离线', last_heartbeat=None):
        self.id = id
        self.equip_code = equip_code  # 设备编码（项目表0.3核心字段）
        self.name = name  # 设备名称（项目表0.3核心字段）
        self.pos_id = pos_id  # 安装地点ID（关联项目表0.2）
        self.person_id = person_id  # 负责人ID（关联项目表0.1）
        self.pur_date = pur_date  # 采购日期
        self.first_time = first_time  # 首次使用日期
        self.use_state = use_state  # 使用状态（在用/在库，项目表0.3）
        self.online_status = online_status  # 在线状态
        self.last_heartbeat = last_heartbeat  # 最后心跳时间

        self.workshop_name = None  # 安装车间名称
        self.person_name = None    # 负责人姓名

    def to_dict(self):
        """关联车间名称、负责人姓名（适配项目表0.2+表0.3）"""
        from models.workshop import Workshop
        from models.staff import Staff
        workshop = Workshop.get_by_id(self.pos_id)
        staff = Staff.get_by_id(self.person_id)
        workshop_name = self.workshop_name if self.workshop_name else (workshop.name if workshop else '')
        return {
            'id': self.id,
            'equip_code': self.equip_code,
            'name': self.name,
            'pos_id': self.pos_id,
            'pos_name': workshop_name,  # 兼容旧版模板
            'workshop_name': workshop_name,  # 兼容新版模板
            'person_id': self.person_id,
            'person_name': self.person_name if self.person_name else (staff.name if staff else ''),
            'pur_date': self.pur_date.strftime('%Y-%m-%d') if hasattr(self.pur_date, 'strftime') and self.pur_date else '',
            'first_time': self.first_time.strftime('%Y-%m-%d') if hasattr(self.first_time, 'strftime') and self.first_time else '',
            'use_state': self.use_state,  # 在用/在库（项目表0.3）
            'online_status': self.online_status,
            'last_heartbeat': self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.last_heartbeat, 'strftime') and self.last_heartbeat else '无'
        }

    @staticmethod
    def get_by_principal_id(principal_id):
        """根据负责人ID查询设备（适配项目表0.3的“负责人”关联）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT ID, Equip_Code, Name, Pos_ID, Person_ID, Pur_Date, First_Time, Use_State, Online_Status, Last_Heartbeat 
            FROM DEV.Dev_Main_Dev 
            WHERE Person_ID = ?
            """
            cursor.execute(sql, (principal_id,))
            rows = cursor.fetchall()
            equipments = []
            for row in rows:
                equipments.append(Equipment(
                    id=row[0],
                    equip_code=row[1],
                    name=row[2],
                    pos_id=row[3],
                    person_id=row[4],
                    pur_date=row[5],
                    first_time=row[6],
                    use_state=row[7],
                    online_status=row[8],
                    last_heartbeat=row[9]
                ))
            return equipments
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_workshop_id(workshop_id):
        """
        根据车间ID（Pos_ID）查询该车间下的所有主设备
        :param workshop_id: 车间/位置ID（Dev_Place表的主键，对应Dev_Main_Dev的Pos_ID）
        :return: list[Equipment] - 设备对象列表，无数据/查询失败返回空列表
        """
        # 1. 参数校验：避免无效查询
        if not workshop_id or not isinstance(workshop_id, (int, str)):
            print(f"车间ID参数无效：{workshop_id}（需为整数/字符串类型）")
            return []

        conn = None
        cursor = None
        equipment_list = []

        try:
            # 2. 获取数据库连接并执行查询（适配Dev_Main_Dev表结构）
            conn = get_db_connection()
            cursor = conn.cursor()

            # 核心SQL：匹配Dev_Main_Dev表的所有字段，Pos_ID关联车间/位置
            sql = """
                SELECT 
                    ID,          -- 主键ID
                    Equip_Code,  -- 设备编码
                    Name,        -- 设备名称
                    Pos_ID,      -- 关联车间/位置ID（原Workshop_ID）
                    Person_ID,   -- 负责人ID
                    Pur_Date,    -- 采购日期
                    First_Time,  -- 首次使用日期
                    Use_State,   -- 使用状态（在用/停用等）
                    Online_Status, -- 在线状态（离线/在线）
                    Last_Heartbeat -- 最后心跳时间
                FROM DEV.Dev_Main_Dev
                WHERE Pos_ID = ?  -- 按车间/位置ID筛选
                ORDER BY Name ASC  -- 按设备名称排序，列表展示更规整
            """
            cursor.execute(sql, [workshop_id])
            rows = cursor.fetchall()

            # 3. 封装为Equipment对象（适配新表字段）
            for row in rows:
                equip = Equipment()
                equip.id = row[0]  # 设备ID
                equip.equip_code = row[1]  # 新增：设备编码
                equip.name = row[2]  # 设备名称
                equip.workshop_id = row[3]  # 映射Pos_ID为workshop_id（兼容原有逻辑）
                equip.person_id = row[4]  # 新增：负责人ID
                equip.pur_date = row[5]  # 新增：采购日期
                equip.first_time = row[6]  # 新增：首次使用日期
                equip.use_state = row[7]  # 新增：使用状态（在用/停用）
                equip.online_status = row[8]  # 新增：在线状态（离线/在线）
                equip.last_heartbeat = row[9]  # 新增：最后心跳时间
                # 兼容原有status字段（可选，避免模板报错）
                equip.status = 1 if equip.use_state == '在用' else 0

                equipment_list.append(equip)

            print(f"车间{workshop_id}查询到{len(equipment_list)}台设备")
            return equipment_list

        except Exception as e:
            # 4. 异常捕获：记录详细日志，避免程序崩溃
            print(f"按车间ID查询设备失败：车间ID={workshop_id}，错误信息={str(e)}")
            return []

        finally:
            # 5. 资源释放：确保游标和连接关闭，防止泄露
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
    def get_by_equip_code(equip_code):
        """根据设备编码查询设备（项目表0.3核心查询）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
            SELECT ID, Equip_Code, Name, Pos_ID, Person_ID, Pur_Date, First_Time, Use_State, Online_Status, Last_Heartbeat 
            FROM DEV.Dev_Main_Dev 
            WHERE Equip_Code = ?
            """
            cursor.execute(sql, (equip_code,))
            row = cursor.fetchone()
            if not row:
                return None
            return Equipment(
                id=row[0],
                equip_code=row[1],
                name=row[2],
                pos_id=row[3],
                person_id=row[4],
                pur_date=row[5],
                first_time=row[6],
                use_state=row[7],
                online_status=row[8],
                last_heartbeat=row[9]
            )
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def count_all():
        """获取设备总数"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT COUNT(*) FROM DEV.Dev_Main_Dev"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def count_online():
        """获取在线设备数量"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT COUNT(*) FROM DEV.Dev_Main_Dev WHERE Online_Status = ?"
            cursor.execute(sql, ('在线',))
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
            conn.close()

    # 原有核心方法保留（get_all、get_by_id、update_heartbeat、check_online_status等）
    @staticmethod
    def get_all(workshop_id=None, use_state=None, page=1, page_size=10):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 构建基础查询SQL
            base_sql = """
                    SELECT 
                        dm.ID, 
                        dm.Equip_Code, 
                        dm.Name, 
                        dm.Pos_ID, 
                        dp.Name AS workshop_name,  -- 车间名称（Dev_Place）
                        dm.Person_ID, 
                        dper.Name AS person_name, -- 负责人姓名（Dev_Person）
                        dm.Pur_Date, 
                        dm.First_Time, 
                        dm.Use_State, 
                        dm.Online_Status, 
                        dm.Last_Heartbeat
                    FROM DEV.Dev_Main_Dev dm
                    LEFT JOIN DEV.Dev_Place dp ON dm.Pos_ID = dp.ID  -- 关联车间表
                    LEFT JOIN DEV.Dev_Person dper ON dm.Person_ID = dper.ID  -- 关联人员表
                """
            count_sql = "SELECT COUNT(*) FROM DEV.Dev_Main_Dev dm"
            
            params = []
            # 重构WHERE条件（避免多个if嵌套，更健壮）
            conditions = []
            if workshop_id:
                conditions.append("dm.Pos_ID = ?")  # 加上表别名dm，避免字段冲突
                params.append(workshop_id)
            if use_state:
                conditions.append("dm.Use_State = ?")
                params.append(use_state)

            # 拼接条件（核心修正2：用AND连接原有关联条件+筛选条件）
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_sql += where_clause
                count_sql += where_clause

            # 执行计数查询
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()[0]

            # 添加分页逻辑
            start_index = (page - 1) * page_size
            base_sql += " ORDER BY dm.ID DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([start_index, page_size])

            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            equipments = []
            for row in rows:
                # 核心修正3：先实例化（用原有参数），再赋值临时属性（避免__init__报错）
                equip = Equipment(
                    id=row[0],
                    equip_code=row[1],
                    name=row[2],
                    pos_id=row[3],
                    person_id=row[5],
                    pur_date=row[7],
                    first_time=row[8],
                    use_state=row[9],
                    online_status=row[10],
                    last_heartbeat=row[11]
                )
                # 赋值临时属性（关联查询的名称）
                equip.workshop_name = row[4]  # 安装车间名称
                equip.person_name = row[6]  # 负责人姓名
                equipments.append(equip)
            return equipments, total_count
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_heartbeat(equipment_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "UPDATE DEV.Dev_Main_Dev SET Last_Heartbeat = CURRENT_TIMESTAMP, Online_Status = '在线' WHERE ID = ?"
            cursor.execute(sql, (equipment_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_online_status():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Last_Heartbeat FROM DEV.Dev_Main_Dev WHERE Online_Status = '在线'"
            cursor.execute(sql)
            rows = cursor.fetchall()
            offline_ids = []
            now = datetime.now()
            for row in rows:
                equipment_id = row[0]
                last_heartbeat = row[1]
                if not last_heartbeat:
                    offline_ids.append(equipment_id)
                    continue
                timeout = (now - last_heartbeat).total_seconds()
                if timeout > HEARTBEAT_TIMEOUT:
                    offline_ids.append(equipment_id)

            if offline_ids:
                placeholders = ', '.join(['?'] * len(offline_ids))
                sql_update = f"UPDATE DEV.Dev_Main_Dev SET Online_Status = '离线' WHERE ID IN ({placeholders})"
                cursor.execute(sql_update, offline_ids)
                conn.commit()
            return len(offline_ids)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add(equip_code, name, pos_id, person_id, pur_date, first_time, use_state):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 查询最大ID
            cursor.execute("SELECT MAX(ID) FROM DEV.Dev_Main_Dev")
            max_id = cursor.fetchone()[0]
            new_id = max_id + 1 if max_id is not None else 1
            
            # 插入新设备
            sql = "INSERT INTO DEV.Dev_Main_Dev (ID, Equip_Code, Name, Pos_ID, Person_ID, Pur_Date, First_Time, Use_State, Online_Status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (new_id, equip_code, name, pos_id, person_id, pur_date, first_time, use_state, '离线'))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(equipment_id, name, pos_id, person_id, pur_date, first_time, use_state):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "UPDATE DEV.Dev_Main_Dev SET Name = ?, Pos_ID = ?, Person_ID = ?, Pur_Date = ?, First_Time = ?, Use_State = ? WHERE ID = ?"
            cursor.execute(sql, (name, pos_id, person_id, pur_date, first_time, use_state, equipment_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(equipment_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "DELETE FROM DEV.Dev_Main_Dev WHERE ID = ?"
            cursor.execute(sql, (equipment_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(equipment_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, Equip_Code, Name, Pos_ID, Person_ID, Pur_Date, First_Time, Use_State, Online_Status, Last_Heartbeat FROM DEV.Dev_Main_Dev WHERE ID = ?"
            cursor.execute(sql, (equipment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Equipment(
                id=row[0],
                equip_code=row[1],
                name=row[2],
                pos_id=row[3],
                person_id=row[4],
                pur_date=row[5],
                first_time=row[6],
                use_state=row[7],
                online_status=row[8],
                last_heartbeat=row[9]
            )
        finally:
            cursor.close()
            conn.close()
