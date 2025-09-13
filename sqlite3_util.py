# 核心库导入
import os
import sqlite3

# 类型提示（仅用于开发时的类型检查）
try:
    from typing import List, Dict, Optional, Union, Tuple
except ImportError:
    # 兼容旧版本Python，定义空类型
    class _DummyType:
        def __getitem__(self, item):
            return self
    List = Dict = Optional = Union = Tuple = _DummyType()
# 创建数据库
def create_db(db_path='system.db'):
    try:
        if not os.path.exists(db_path):
            # 创建空数据库文件
            open(db_path, 'w').close()
            print(f"已创建空数据库: {os.path.abspath(db_path)}")
            return True
        else:
            print(f"数据库已存在: {os.path.abspath(db_path)}")
            return False
    except Exception as e:
        print(f"创建数据库失败: {str(e)}")
        return False

from typing import List, Optional

def create_table(
    db_path: str = 'system.db',
    table_name: str = None,
    columns: List[dict] = None,
    sql_statement: str = None
) -> bool:
    """
    在SQLite数据库中创建表
    
    参数:
        db_path: 数据库文件路径 (默认'system.db')
        table_name: 要创建的表名
        columns: 列定义列表 [{'name': 'id', 'type': 'INTEGER', 'constraints': 'PRIMARY KEY'}, ...]
        sql_statement: 直接提供完整的CREATE TABLE语句
        
    返回:
        bool: 是否创建成功
        
    注意:
        必须提供 columns 或 sql_statement 其中之一
    """
    if not (columns or sql_statement):
        print("错误：必须提供列定义或完整SQL语句")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if sql_statement:
            # 使用直接提供的SQL语句
            cursor.execute(sql_statement)
        else:
            # 动态生成SQL语句
            columns_def = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if 'constraints' in col:
                    col_def += f" {col['constraints']}"
                columns_def.append(col_def)
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_def)})"
            cursor.execute(create_sql)
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"创建表失败: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def table_exists(db_path: str, table_name: str) -> bool:
    """
    检查表是否已存在
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        return cursor.fetchone() is not None
    finally:
        conn.close()

def init_users_table(db_path: str = 'system.db') -> bool:
    """
    初始化 users 表
    包含字段：id, file_name, username, intro, unique_id, cmm_id, code, create_time
    """
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        username TEXT NOT NULL,
        intro TEXT,
        unique_id TEXT,
        cmm_id TEXT,
        code TEXT,
        create_time TEXT NOT NULL
    )
    """

    try:
        if not table_exists(db_path, 'users'):
            result = create_table(db_path=db_path, sql_statement=users_table_sql)
            if result:
                print("✅ users 表创建成功")
                return True
            else:
                print("❌ users 表创建失败")
                return False
        else:
            print("ℹ️  users 表已存在，跳过创建")
            return True
    except Exception as e:
        print(f"❌ 初始化 users 表失败: {str(e)}")
        return False

def init_tokens_table(db_path: str = 'system.db') -> bool:
    """
    初始化 tokens 表
    包含字段：id, token, create_time
    """
    tokens_table_sql = """
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL UNIQUE,
        create_time TEXT NOT NULL
    )
    """

    try:
        if not table_exists(db_path, 'tokens'):
            result = create_table(db_path=db_path, sql_statement=tokens_table_sql)
            if result:
                print("✅ tokens 表创建成功")
                return True
            else:
                print("❌ tokens 表创建失败")
                return False
        else:
            print("ℹ️  tokens 表已存在，跳过创建")
            return True
    except Exception as e:
        print(f"❌ 初始化 tokens 表失败: {str(e)}")
        return False

def init_wechat_phrases_table(db_path: str = 'system.db') -> bool:
    """
    初始化微信常用语表
    """
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS wechat_phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status INTEGER DEFAULT 1
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql)

        if result:
            # 插入一些默认的常用语
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查是否已有数据
            cursor.execute("SELECT COUNT(*) FROM wechat_phrases")
            count = cursor.fetchone()[0]

            if count == 0:
                default_phrases = [
                    "你好，希望能加个好友！",
                    "您好，我是通过朋友介绍认识您的，希望能成为朋友。",
                    "Hi，看到您的朋友圈很有趣，想和您交个朋友。",
                    "您好，我们有共同的朋友，希望能认识一下。",
                    "你好，想和您交流学习一下，请多指教！"
                ]

                for phrase in default_phrases:
                    cursor.execute(
                        "INSERT INTO wechat_phrases (content) VALUES (?)",
                        (phrase,)
                    )

                conn.commit()
                print("✅ 已插入默认常用语")

            conn.close()
            print("ℹ️  wechat_phrases 表初始化成功")
            return True
        else:
            print("ℹ️  wechat_phrases 表已存在，跳过创建")
            return True
    except Exception as e:
        print(f"❌ 初始化 wechat_phrases 表失败: {str(e)}")
        return False

def init_adduser_logs_table(db_path: str = 'system.db') -> bool:
    """
    初始化添加用户日志表
    包含字段：微信号、验证消息、添加时间、状态、截图、错误信息
    """
    try:
        if table_exists(db_path, 'adduser_logs'):
            print("ℹ️  adduser_logs 表已存在，跳过创建")
            return True

        sql_statement = '''
            CREATE TABLE IF NOT EXISTS adduser_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wechat_id TEXT NOT NULL,
                verify_msg TEXT,
                add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status INTEGER DEFAULT 0,
                img_path TEXT,
                error_msg TEXT,
                remark_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''

        result = create_table(
            db_path=db_path,
            sql_statement=sql_statement
        )

        if result:
            print("✅ adduser_logs 表初始化成功")
            return True
        else:
            print("❌ adduser_logs 表创建失败")
            return False

    except Exception as e:
        print(f"❌ 初始化 adduser_logs 表失败: {str(e)}")
        return False

def init_database(db_path: str = 'system.db') -> bool:
    """
    初始化数据库和所有表
    """
    print("🚀 开始初始化数据库...")

    # 1. 创建数据库文件
    create_db(db_path)

    # 2. 创建所有表
    tables_success = []

    # 创建 users 表
    users_result = init_users_table(db_path)
    tables_success.append(('users', users_result))

    # 创建 tokens 表
    tokens_result = init_tokens_table(db_path)
    tables_success.append(('tokens', tokens_result))

    # 创建 wechat_phrases 表
    phrases_result = init_wechat_phrases_table(db_path)
    tables_success.append(('wechat_phrases', phrases_result))

    # 创建 adduser_logs 表
    adduser_logs_result = init_adduser_logs_table(db_path)
    tables_success.append(('adduser_logs', adduser_logs_result))

    # 创建 rooms 表（直播间表）
    rooms_result = init_rooms_table(db_path)
    tables_success.append(('rooms', rooms_result))

    # 创建 speech 表（话术表）
    speech_result = init_speech_table(db_path)
    tables_success.append(('speech', speech_result))

    # 创建 room_speeches 表（直播间话术关联表）
    room_speeches_result = init_room_speeches_table(db_path)
    tables_success.append(('room_speeches', room_speeches_result))

    # 创建 time_of_live 表（直播时间表）
    time_of_live_result = init_time_of_live_table(db_path)
    tables_success.append(('time_of_live', time_of_live_result))

    # 创建 tasks 表（定时任务表）
    tasks_result = init_tasks_table(db_path)
    tables_success.append(('tasks', tasks_result))

    # 创建 task_log 表（任务日志表）
    task_log_result = init_task_log_table(db_path)
    tables_success.append(('task_log', task_log_result))

    # 创建 products 表（商品表）
    products_result = init_products_table(db_path)
    tables_success.append(('products', products_result))

    # 创建 images 表（图片表）
    images_result = init_images_table(db_path)
    tables_success.append(('images', images_result))

    # 统计结果
    success_count = sum(1 for _, success in tables_success if success)
    total_count = len(tables_success)

    print(f"\n📊 数据库初始化完成:")
    print(f"   数据库文件: {os.path.abspath(db_path)}")
    print(f"   表创建结果: {success_count}/{total_count} 成功")

    for table_name, success in tables_success:
        status = "✅" if success else "❌"
        print(f"   {status} {table_name}")

    return success_count == total_count

def query_wechat_phrases(db_path: str = 'system.db', status: int = None) -> List[Dict]:
    """
    查询微信常用语
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status is not None:
            cursor.execute(
                "SELECT * FROM wechat_phrases WHERE status = ? ORDER BY create_time DESC",
                (status,)
            )
        else:
            cursor.execute("SELECT * FROM wechat_phrases ORDER BY create_time DESC")

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"查询常用语失败: {str(e)}")
        return []

def add_wechat_phrase(db_path: str = 'system.db', content: str = '') -> bool:
    """
    添加微信常用语
    """
    try:
        if not content.strip():
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO wechat_phrases (content) VALUES (?)",
            (content.strip(),)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"添加常用语失败: {str(e)}")
        return False

def update_wechat_phrase(db_path: str = 'system.db', phrase_id: int = None, content: str = '', status: int = None) -> bool:
    """
    更新微信常用语
    """
    try:
        if phrase_id is None:
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if content and status is not None:
            cursor.execute(
                "UPDATE wechat_phrases SET content = ?, status = ? WHERE id = ?",
                (content.strip(), status, phrase_id)
            )
        elif content:
            cursor.execute(
                "UPDATE wechat_phrases SET content = ? WHERE id = ?",
                (content.strip(), phrase_id)
            )
        elif status is not None:
            cursor.execute(
                "UPDATE wechat_phrases SET status = ? WHERE id = ?",
                (status, phrase_id)
            )
        else:
            return False

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"更新常用语失败: {str(e)}")
        return False

def delete_wechat_phrase(db_path: str = 'system.db', phrase_id: int = None) -> bool:
    """
    删除微信常用语
    """
    try:
        if phrase_id is None:
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM wechat_phrases WHERE id = ?", (phrase_id,))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"删除常用语失败: {str(e)}")
        return False

def query_users(db_path: str = 'system.db', limit: int = None) -> List[Dict]:
    """
    查询 users 表数据
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if limit:
            cursor.execute("SELECT * FROM users ORDER BY create_time DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT * FROM users ORDER BY create_time DESC")

        results = [dict(row) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"查询 users 表失败: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def get_users_count(db_path: str = 'system.db') -> int:
    """
    获取 users 表总记录数
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(f"获取 users 表记录数失败: {str(e)}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def verify_insert_result(db_path: str = 'system.db') -> Dict:
    """
    验证插入结果，检查数据库状态
    """
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            return {
                "success": False,
                "message": f"数据库文件不存在: {db_path}",
                "file_exists": False,
                "table_exists": False,
                "record_count": 0
            }

        # 检查表是否存在
        table_exists_flag = table_exists(db_path, 'users')

        # 获取记录数
        record_count = get_users_count(db_path) if table_exists_flag else 0

        # 获取最新几条记录
        latest_records = query_users(db_path, 5) if table_exists_flag else []

        return {
            "success": True,
            "message": f"数据库验证完成",
            "file_exists": True,
            "table_exists": table_exists_flag,
            "record_count": record_count,
            "latest_records": latest_records,
            "db_path": os.path.abspath(db_path)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"验证失败: {str(e)}",
            "error": str(e)
        }

def query_table(
    db_path: str,
    table_name: str,
    columns: List[str] = ["*"],
    where: Optional[str] = None,
    params: Optional[Union[tuple, dict]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    通用SQLite表查询方法
    
    参数:
        db_path: 数据库文件路径
        table_name: 要查询的表名
        columns: 要查询的列名列表，默认查询所有列
        where: WHERE条件语句（不包含WHERE关键字）
        params: 查询参数（元组或字典）
        order_by: 排序条件（不包含ORDER BY关键字）
        limit: 返回结果数量限制
        
    返回:
        包含查询结果的字典列表，每个字典代表一行数据
    """
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使返回结果为字典形式
        cursor = conn.cursor()
        
        # 构建SQL语句
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
        
        # 执行查询
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 获取结果并转换为字典列表
        results = [dict(row) for row in cursor.fetchall()]
        return results
        
    except sqlite3.Error as e:
        print(f"查询表 {table_name} 失败: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def batch_insert(
    db_path: str,
    table_name: str,
    field_names: List[str],
    data: List[Tuple],
    batch_size: int = 100
) -> int:
    """
    指定表名的批量数据插入方法
    
    参数:
        db_path: 数据库文件路径
        table_name: 要插入数据的表名
        field_names: 字段名称列表
        data: 要插入的数据列表（每个元素是字段值的元组）
        batch_size: 每批插入的数据量（默认100）
        
    返回:
        成功插入的行数
    """
    inserted_rows = 0
    conn = None
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 构建INSERT语句
        placeholders = ', '.join(['?'] * len(field_names))
        sql = f"""
        INSERT INTO {table_name} 
        ({', '.join(field_names)})
        VALUES ({placeholders})
        """
        
        # 分批执行插入
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            cursor.executemany(sql, batch)
            inserted_rows += len(batch)
            conn.commit()  # 每批提交一次
            
        return inserted_rows
        
    except sqlite3.Error as e:
        print(f"批量插入到表 {table_name} 失败: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()


def add_user_log(db_path: str = 'system.db', wechat_id: str = '', user_id: int = None,
                 status: int = 0, img_path: str = '', verify_msg: str = '',
                 error_msg: str = '', remark_name: str = '') -> bool:
    """
    添加用户操作日志

    参数:
        wechat_id: 微信号
        verify_msg: 验证消息
        status: 状态 (0=失败, 1=成功)
        img_path: 截图路径
        error_msg: 错误信息
        remark_name: 备注名称
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO adduser_logs (user_id, wechat_id, verify_msg, status, img_path, error_msg, remark_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, wechat_id, verify_msg, status, img_path, error_msg, remark_name))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"添加用户日志失败: {str(e)}")
        return False

def query_user_logs(db_path: str = 'system.db', limit: int = 100) -> List[Dict]:
    """
    查询用户操作日志
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT l.*, u.unique_id as user_unique_id, u.username, u.intro
            FROM adduser_logs l
            LEFT JOIN users u ON l.user_id = u.id
            ORDER BY l.add_time DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"查询用户日志失败: {str(e)}")
        return []

def clear_user_logs(db_path: str = 'system.db') -> bool:
    """
    清空用户操作日志
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM adduser_logs')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"清空用户日志失败: {str(e)}")
        return False

def check_user_added(db_path: str = 'system.db', wechat_id: str = '') -> bool:
    """
    检查用户是否已经添加过（成功状态）
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM adduser_logs
            WHERE wechat_id = ? AND status = 1
        ''', (wechat_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"检查用户添加状态失败: {str(e)}")
        return False

def check_existing_ids_in_users(db_path, file_name, cmm_ids):
    """
    检查给定的蝉妈妈ID列表中哪些已经存在于users表中
    :param db_path: 数据库路径
    :param file_name: 文件名
    :param cmm_ids: 蝉妈妈ID列表
    :return: 字典 {'existing_ids': [...], 'new_ids': [...]}
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            conn.close()
            return {'existing_ids': [], 'new_ids': cmm_ids}

        existing_ids = []
        new_ids = []

        for cmm_id in cmm_ids:
            # 检查该ID是否已存在于指定文件名的记录中
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE file_name = ? AND cmm_id = ?",
                (file_name, cmm_id)
            )
            count = cursor.fetchone()[0]

            if count > 0:
                existing_ids.append(cmm_id)
            else:
                new_ids.append(cmm_id)

        conn.close()

        print(f"📊 ID检查结果:")
        print(f"   文件: {file_name}")
        print(f"   总ID数: {len(cmm_ids)}")
        print(f"   已存在: {len(existing_ids)}")
        print(f"   需处理: {len(new_ids)}")

        return {
            'existing_ids': existing_ids,
            'new_ids': new_ids,
            'total_count': len(cmm_ids),
            'existing_count': len(existing_ids),
            'new_count': len(new_ids)
        }

    except Exception as e:
        print(f"❌ 检查已存在ID失败: {str(e)}")
        return {'existing_ids': [], 'new_ids': cmm_ids}

def save_partial_data_with_confirmation(db_path, table_name, field_names, data, processed_count, total_count):
    """
    保存部分处理的数据，并返回确认信息
    :param db_path: 数据库路径
    :param table_name: 表名
    :param field_names: 字段名列表
    :param data: 要插入的数据
    :param processed_count: 已处理数量
    :param total_count: 总数量
    :return: 保存结果和确认信息
    """
    try:
        if not data:
            return {
                'success': False,
                'message': '没有数据需要保存',
                'processed_count': processed_count,
                'total_count': total_count
            }

        # 执行批量插入
        inserted_count = batch_insert(db_path, table_name, field_names, data)

        if inserted_count > 0:
            return {
                'success': True,
                'message': f'成功保存 {inserted_count} 条数据到数据库',
                'inserted_count': inserted_count,
                'processed_count': processed_count,
                'total_count': total_count,
                'completion_rate': round((processed_count / total_count) * 100, 1) if total_count > 0 else 0
            }
        else:
            return {
                'success': False,
                'message': '数据保存失败',
                'processed_count': processed_count,
                'total_count': total_count
            }

    except Exception as e:
        print(f"❌ 保存部分数据失败: {str(e)}")
        return {
            'success': False,
            'message': f'保存失败: {str(e)}',
            'processed_count': processed_count,
            'total_count': total_count
        }

def init_rooms_table(db_path: str = 'system.db') -> bool:
    """
    初始化 rooms 表（直播间表）
    字段：id, name, platform, create_time, status, product_id
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                    -- 直播间名称
            platform TEXT NOT NULL,               -- 平台类型：wechat/douyin/kuaishou
            create_time TEXT NOT NULL,             -- 创建时间
            status INTEGER DEFAULT 1,              -- 状态：1=启用，0=禁用
            product_id INTEGER,                    -- 绑定的商品ID
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ rooms 表初始化成功")

            # 数据库字段迁移
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 检查字段是否存在
                cursor.execute("PRAGMA table_info(rooms)")
                columns = [column[1] for column in cursor.fetchall()]

                needs_migration = False

                # 检查是否需要删除 next_live_time 字段
                if 'next_live_time' in columns:
                    needs_migration = True
                    print("⚠️ 检测到旧的 next_live_time 字段，需要迁移")

                # 检查是否需要添加 product_id 字段
                if 'product_id' not in columns:
                    needs_migration = True
                    print("⚠️ 检测到缺少 product_id 字段，需要迁移")

                if needs_migration:
                    # 创建新表（包含所有最新字段）
                    cursor.execute("""
                        CREATE TABLE rooms_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            platform TEXT NOT NULL,
                            create_time TEXT NOT NULL,
                            status INTEGER DEFAULT 1,
                            product_id INTEGER,
                            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
                        )
                    """)

                    # 复制数据（只复制存在的字段）
                    cursor.execute("""
                        INSERT INTO rooms_new (id, name, platform, create_time, status)
                        SELECT id, name, platform, create_time, status FROM rooms
                    """)

                    # 删除旧表，重命名新表
                    cursor.execute("DROP TABLE rooms")
                    cursor.execute("ALTER TABLE rooms_new RENAME TO rooms")

                    print("✅ rooms 表字段迁移成功")

                conn.commit()
                conn.close()

            except Exception as e:
                print(f"⚠️ rooms 表字段迁移失败: {str(e)}")
        return result

    except Exception as e:
        print(f"❌ 初始化 rooms 表失败: {str(e)}")
        return False

def init_speech_table(db_path: str = 'system.db') -> bool:
    """
    初始化 speech 表（话术表）
    字段：id, content, create_time, status
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS speech (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,                 -- 话术内容
            create_time TEXT NOT NULL,             -- 创建时间
            status INTEGER DEFAULT 1               -- 状态：1=启用，0=禁用
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ speech 表初始化成功")

            # 检查并删除 room_id 字段（数据库迁移）
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 检查字段是否存在
                cursor.execute("PRAGMA table_info(speech)")
                columns = [column[1] for column in cursor.fetchall()]

                if 'room_id' in columns:
                    # 创建新表
                    cursor.execute("""
                        CREATE TABLE speech_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            content TEXT NOT NULL,
                            create_time TEXT NOT NULL,
                            status INTEGER DEFAULT 1
                        )
                    """)

                    # 复制数据
                    cursor.execute("""
                        INSERT INTO speech_new (id, content, create_time, status)
                        SELECT id, content, create_time, status FROM speech
                    """)

                    # 删除旧表，重命名新表
                    cursor.execute("DROP TABLE speech")
                    cursor.execute("ALTER TABLE speech_new RENAME TO speech")
                    print("✅ speech 表字段迁移成功")

                conn.commit()
                conn.close()

            except Exception as e:
                print(f"⚠️ speech 表字段迁移失败: {str(e)}")
        return result

    except Exception as e:
        print(f"❌ 初始化 speech 表失败: {str(e)}")
        return False

def init_room_speeches_table(db_path: str = 'system.db') -> bool:
    """
    初始化 room_speeches 表（直播间话术关联表）
    字段：id, room_id, speech_id, create_time, status
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS room_speeches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,              -- 直播间ID
            speech_id INTEGER NOT NULL,            -- 话术ID
            create_time TEXT NOT NULL,             -- 绑定时间
            status INTEGER DEFAULT 1,              -- 启用状态：1=启用，0=禁用
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (speech_id) REFERENCES speech(id) ON DELETE CASCADE,
            UNIQUE(room_id, speech_id)             -- 防止重复绑定
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ room_speeches 表初始化成功")
        return result

    except Exception as e:
        print(f"❌ 初始化 room_speeches 表失败: {str(e)}")
        return False

def init_time_of_live_table(db_path: str = 'system.db') -> bool:
    """
    初始化 time_of_live 表（直播时间表）
    字段：id, room_id, live_time, create_time, status, remark
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS time_of_live (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,              -- 直播间ID
            live_time TEXT NOT NULL,               -- 直播时间
            create_time TEXT NOT NULL,             -- 创建时间
            status INTEGER DEFAULT 0,              -- 状态：0=等待开播，1=已开播
            remark TEXT,                           -- 备注
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ time_of_live 表初始化成功")

        return result

    except Exception as e:
        print(f"❌ 初始化 time_of_live 表失败: {str(e)}")
        return False

# ==================== 直播间管理 CRUD ====================

def add_room(db_path: str = 'system.db', name: str = '', platform: str = '', status: int = 1, product_id: int = None) -> bool:
    """
    添加直播间
    """
    try:
        from datetime import datetime

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO rooms (name, platform, create_time, status, product_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, platform, create_time, status, product_id))

        conn.commit()
        conn.close()

        print(f"✅ 成功添加直播间: {name} ({platform})")
        return True

    except Exception as e:
        print(f"❌ 添加直播间失败: {str(e)}")
        return False

def query_rooms(db_path: str = 'system.db', platform: str = None, status: int = None) -> List[Dict]:
    """
    查询直播间列表（联表查询商品信息）
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_conditions = []
        params = []

        if platform:
            where_conditions.append("r.platform = ?")
            params.append(platform)

        if status is not None:
            where_conditions.append("r.status = ?")
            params.append(status)

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 联表查询商品信息
        sql = f"""
            SELECT r.*,
                   p.name as product_name,
                   p.cover as product_cover,
                   p.price as product_price
            FROM rooms r
            LEFT JOIN products p ON r.product_id = p.id
            {where_clause}
            ORDER BY r.create_time DESC
        """
        cursor.execute(sql, params)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    except Exception as e:
        print(f"❌ 查询直播间失败: {str(e)}")
        return []

def update_room(db_path: str = 'system.db', room_id: int = 0, name: str = None, platform: str = None, status: int = None, product_id: int = None, update_product_id: bool = False) -> bool:
    """
    更新直播间信息
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        update_fields = []
        params = []

        if name is not None:
            update_fields.append("name = ?")
            params.append(name)

        if platform is not None:
            update_fields.append("platform = ?")
            params.append(platform)

        if status is not None:
            update_fields.append("status = ?")
            params.append(status)

        # 修复product_id更新逻辑：使用update_product_id标志来明确是否要更新product_id
        if update_product_id:
            update_fields.append("product_id = ?")
            params.append(product_id)
            print(f"🔄 更新product_id: {product_id}")

        if not update_fields:
            print("❌ 没有要更新的字段")
            return False

        params.append(room_id)

        sql = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = ?"
        print(f"🔄 执行SQL: {sql}, 参数: {params}")
        cursor.execute(sql, params)

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            print(f"✅ 成功更新直播间: ID={room_id}, 影响行数: {cursor.rowcount}")
            return True
        else:
            conn.close()
            print(f"❌ 更新直播间失败: 没有找到ID={room_id}的直播间")
            return False

    except Exception as e:
        print(f"❌ 更新直播间失败: {str(e)}")
        return False

def delete_room(db_path: str = 'system.db', room_id: int = 0) -> bool:
    """
    删除直播间
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 先删除关联的绑定关系
        cursor.execute("DELETE FROM room_speeches WHERE room_id = ?", (room_id,))

        # 再删除直播间
        cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))

        conn.commit()
        conn.close()

        print(f"✅ 成功删除直播间: ID={room_id}")
        return True

    except Exception as e:
        print(f"❌ 删除直播间失败: {str(e)}")
        return False

# ==================== 话术管理 CRUD ====================

def add_speech(db_path: str = 'system.db', content: str = '', status: int = 1) -> bool:
    """
    添加话术
    """
    try:
        from datetime import datetime

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO speech (content, create_time, status)
            VALUES (?, ?, ?)
        """, (content, create_time, status))

        conn.commit()
        conn.close()

        print(f"✅ 成功添加话术: {content[:20]}...")
        return True

    except Exception as e:
        print(f"❌ 添加话术失败: {str(e)}")
        return False

def query_speech(db_path: str = 'system.db', status: int = None, search: str = None) -> List[Dict]:
    """
    查询话术列表
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_conditions = []
        params = []

        if status is not None:
            where_conditions.append("status = ?")
            params.append(status)

        if search is not None and search.strip():
            where_conditions.append("content LIKE ?")
            params.append(f"%{search.strip()}%")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 简单查询话术表
        sql = f"""
            SELECT *
            FROM speech
            {where_clause}
            ORDER BY create_time DESC
        """
        cursor.execute(sql, params)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    except Exception as e:
        print(f"❌ 查询话术失败: {str(e)}")
        return []

def update_speech(db_path: str = 'system.db', speech_id: int = 0, content: str = None, status: int = None) -> bool:
    """
    更新话术信息
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        update_fields = []
        params = []

        if content is not None:
            update_fields.append("content = ?")
            params.append(content)

        if status is not None:
            update_fields.append("status = ?")
            params.append(status)

        if not update_fields:
            return False

        params.append(speech_id)

        sql = f"UPDATE speech SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(sql, params)

        conn.commit()
        conn.close()

        print(f"✅ 成功更新话术: ID={speech_id}")
        return True

    except Exception as e:
        print(f"❌ 更新话术失败: {str(e)}")
        return False

def delete_speech(db_path: str = 'system.db', speech_id: int = 0) -> bool:
    """
    删除话术
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM speech WHERE id = ?", (speech_id,))

        conn.commit()
        conn.close()

        print(f"✅ 成功删除话术: ID={speech_id}")
        return True

    except Exception as e:
        print(f"❌ 删除话术失败: {str(e)}")
        return False

def init_tasks_table(db_path: str = 'system.db') -> bool:
    """
    初始化 tasks 表（定时任务表）
    字段：id, task_id, task_type, room_id, run_time, create_time, status, remark
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,           -- APScheduler任务ID
            task_type TEXT NOT NULL,                -- 任务类型：live_reminder等
            room_id INTEGER,                        -- 关联的直播间ID
            run_time TEXT NOT NULL,                 -- 执行时间
            create_time TEXT NOT NULL,              -- 创建时间
            status INTEGER DEFAULT 1,               -- 状态：1=有效，0=无效
            remark TEXT,                            -- 备注信息
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ tasks 表初始化成功")

        return result

    except Exception as e:
        print(f"❌ 初始化 tasks 表失败: {str(e)}")
        return False

def init_task_log_table(db_path: str = 'system.db') -> bool:
    """
    初始化 task_log 表（任务日志表）
    字段：id, task_id, status, message, room_id, room_name, execution_time, create_time
    """
    try:
        sql_statement = """
        CREATE TABLE IF NOT EXISTS task_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,                  -- 关联的任务ID
            status INTEGER NOT NULL,                -- 状态：1=成功，2=失败
            message TEXT,                           -- 状态详情（成功原因或失败原因）
            room_id INTEGER,                        -- 直播间ID
            room_name TEXT,                         -- 直播间名称
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 执行时间
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     -- 创建时间
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
        )
        """

        result = create_table(db_path=db_path, sql_statement=sql_statement)
        if result:
            print("✅ task_log 表初始化成功")

        return result

    except Exception as e:
        print(f"❌ 初始化 task_log 表失败: {str(e)}")
        return False

if __name__ == "__main__":
    print('载入数据库')
    # 插入数据

# ==================== 直播间话术关联管理 CRUD ====================

def bind_speech_to_room(db_path: str = 'system.db', room_id: int = 0, speech_id: int = 0, status: int = 1) -> bool:
    """
    绑定话术到直播间
    """
    try:
        from datetime import datetime

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT OR REPLACE INTO room_speeches (room_id, speech_id, create_time, status)
            VALUES (?, ?, ?, ?)
        """, (room_id, speech_id, create_time, status))

        conn.commit()
        conn.close()

        print(f"✅ 成功绑定话术: 直播间ID={room_id}, 话术ID={speech_id}")
        return True

    except Exception as e:
        print(f"❌ 绑定话术失败: {str(e)}")
        return False

def unbind_speech_from_room(db_path: str = 'system.db', room_id: int = 0, speech_id: int = 0) -> bool:
    """
    解绑话术从直播间
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM room_speeches
            WHERE room_id = ? AND speech_id = ?
        """, (room_id, speech_id))

        conn.commit()
        conn.close()

        print(f"✅ 成功解绑话术: 直播间ID={room_id}, 话术ID={speech_id}")
        return True

    except Exception as e:
        print(f"❌ 解绑话术失败: {str(e)}")
        return False

def get_room_speeches(db_path: str = 'system.db', room_id: int = 0) -> list:
    """
    获取直播间绑定的话术列表
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, rs.status as bind_status, rs.create_time as bind_time
            FROM room_speeches rs
            JOIN speech s ON rs.speech_id = s.id
            WHERE rs.room_id = ? AND rs.status = 1
            ORDER BY rs.create_time DESC
        """, (room_id,))

        rows = cursor.fetchall()

        # 转换为字典列表
        columns = [description[0] for description in cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))

        conn.close()
        return result

    except Exception as e:
        print(f"❌ 查询直播间话术失败: {str(e)}")
        return []

def get_speech_rooms(db_path: str = 'system.db', speech_id: int = 0) -> list:
    """
    获取话术绑定的直播间列表
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.*, rs.status as bind_status, rs.create_time as bind_time
            FROM room_speeches rs
            JOIN rooms r ON rs.room_id = r.id
            WHERE rs.speech_id = ? AND rs.status = 1
            ORDER BY rs.create_time DESC
        """, (speech_id,))

        rows = cursor.fetchall()

        # 转换为字典列表
        columns = [description[0] for description in cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))

        conn.close()
        return result

    except Exception as e:
        print(f"❌ 查询话术绑定直播间失败: {str(e)}")
        return []

def update_room_speech_status(db_path: str = 'system.db', room_id: int = 0, speech_id: int = 0, status: int = 1) -> bool:
    """
    更新直播间话术绑定状态
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE room_speeches
            SET status = ?
            WHERE room_id = ? AND speech_id = ?
        """, (status, room_id, speech_id))

        conn.commit()
        conn.close()

        print(f"✅ 成功更新绑定状态: 直播间ID={room_id}, 话术ID={speech_id}, 状态={status}")
        return True

    except Exception as e:
        print(f"❌ 更新绑定状态失败: {str(e)}")
        return False

# ==================== 直播时间管理 CRUD ====================

def add_live_time(db_path: str = 'system.db', room_id: int = 0, live_time: str = '', remark: str = '') -> bool:
    """
    添加直播时间
    """
    try:
        from datetime import datetime

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查该直播间是否已有等待开播的时间
        cursor.execute("""
            SELECT r.name FROM time_of_live t
            JOIN rooms r ON t.room_id = r.id
            WHERE t.room_id = ? AND t.status = 0
        """, (room_id,))

        existing_room = cursor.fetchone()
        if existing_room:
            conn.close()
            room_name = existing_room[0]
            print(f"❌{room_name}已存在待开播时间")
            raise Exception(f"直播间{room_name}已存在待开播时间")

        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(
            """
            INSERT INTO time_of_live (room_id, live_time, create_time, status, remark)
            VALUES (?, ?, ?, 0, ?)
        """,
            (room_id, live_time, create_time, remark),
        )

        conn.commit()
        conn.close()

        print(f"✅ 成功添加直播时间: 直播间ID={room_id}, 时间={live_time}")
        return True

    except Exception as e:
        print(f"❌ 添加直播时间失败: {str(e)}")
        # 重新抛出异常，让上层处理
        raise e

def get_room_next_live_time(db_path: str = 'system.db', room_id: int = 0) -> dict:
    """
    获取直播间的下次直播时间
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM time_of_live
            WHERE room_id = ? AND status = 0
            ORDER BY live_time ASC
            LIMIT 1
        """, (room_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        else:
            return {}

    except Exception as e:
        print(f"❌ 查询直播时间失败: {str(e)}")
        return {}

def get_room_live_times(db_path: str = 'system.db', room_id: int = 0) -> list:
    """
    获取直播间的所有直播时间
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM time_of_live
            WHERE room_id = ?
            ORDER BY live_time DESC
        """, (room_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        print(f"❌ 查询直播时间列表失败: {str(e)}")
        return []

def update_live_time_status(db_path: str = 'system.db', live_time_id: int = 0, status: int = 1) -> bool:
    """
    更新直播时间状态
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE time_of_live SET status = ? WHERE id = ?
        """, (status, live_time_id))

        conn.commit()
        conn.close()

        print(f"✅ 成功更新直播时间状态: ID={live_time_id}, 状态={status}")
        return True

    except Exception as e:
        print(f"❌ 更新直播时间状态失败: {str(e)}")
        return False

def delete_live_time(db_path: str = 'system.db', live_time_id: int = 0) -> bool:
    """
    删除直播时间
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM time_of_live WHERE id = ?", (live_time_id,))

        conn.commit()
        conn.close()

        print(f"✅ 成功删除直播时间: ID={live_time_id}")
        return True

    except Exception as e:
        print(f"❌ 删除直播时间失败: {str(e)}")
        return False

def init_products_table(db_path: str = 'system.db') -> bool:
    """
    初始化商品表
    字段：id, name, cover, price, create_time, remark
    """
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cover TEXT,
            price DECIMAL(10,2) DEFAULT 0.00,
            create_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            remark TEXT
        )
        """

        result = create_table(
            db_path=db_path,
            sql_statement=sql
        )

        if result:
            print("✅ products 表初始化成功")
        else:
            print("❌ products 表初始化失败")

        return result

    except Exception as e:
        print(f"❌ 初始化 products 表失败: {str(e)}")
        return False

def init_images_table(db_path: str = 'system.db') -> bool:
    """
    初始化图片表
    字段：id, create_time, remark, status, path, product_id
    """
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            create_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            remark TEXT,
            status INTEGER DEFAULT 1,
            path TEXT NOT NULL,
            product_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
        """

        result = create_table(
            db_path=db_path,
            sql_statement=sql
        )

        if result:
            print("✅ images 表初始化成功")

            # 创建索引以提高查询性能
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 为product_id创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_product_id ON images(product_id)")
                # 为status创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_status ON images(status)")
                # 为path创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_path ON images(path)")

                conn.commit()
                conn.close()
                print("✅ images 表索引创建成功")

            except Exception as idx_error:
                print(f"⚠️ images 表索引创建失败: {str(idx_error)}")
        else:
            print("❌ images 表初始化失败")

        return result

    except Exception as e:
        print(f"❌ 初始化 images 表失败: {str(e)}")
        return False

# ==================== 商品管理相关函数 ====================

def add_product(db_path: str = 'system.db', name: str = '', cover: str = '',
                price: float = 0.0, remark: str = '') -> dict:
    """
    添加商品
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products (name, cover, price, remark)
            VALUES (?, ?, ?, ?)
        """, (name, cover, price, remark))

        product_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ 成功添加商品: {name} (ID: {product_id})")
        return {
            'success': True,
            'message': '商品添加成功',
            'product_id': product_id
        }

    except Exception as e:
        print(f"❌ 添加商品失败: {str(e)}")
        return {
            'success': False,
            'message': f'添加商品失败: {str(e)}'
        }

def query_products(db_path: str = 'system.db', page: int = 1, page_size: int = 20,
                   search_name: str = '') -> dict:
    """
    查询商品列表（分页）
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 构建查询条件
        where_clause = ""
        params = []

        if search_name:
            where_clause = "WHERE name LIKE ?"
            params.append(f"%{search_name}%")

        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM products {where_clause}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # 分页查询
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT * FROM products {where_clause}
            ORDER BY create_time DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, params + [page_size, offset])
        products = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'success': True,
            'data': products,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"❌ 查询商品失败: {str(e)}")
        return {
            'success': False,
            'message': f'查询商品失败: {str(e)}',
            'data': [],
            'total': 0
        }

def update_product(db_path: str = 'system.db', product_id: int = 0,
                   name: str = '', cover: str = '', price: float = 0.0,
                   remark: str = '') -> dict:
    """
    更新商品信息
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE products
            SET name = ?, cover = ?, price = ?, remark = ?
            WHERE id = ?
        """, (name, cover, price, remark, product_id))

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            print(f"✅ 成功更新商品: ID={product_id}")
            return {
                'success': True,
                'message': '商品更新成功'
            }
        else:
            conn.close()
            return {
                'success': False,
                'message': '商品不存在'
            }

    except Exception as e:
        print(f"❌ 更新商品失败: {str(e)}")
        return {
            'success': False,
            'message': f'更新商品失败: {str(e)}'
        }

def delete_product(db_path: str = 'system.db', product_id: int = 0) -> dict:
    """
    删除商品（同时将关联的图片的product_id设为NULL）
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 先检查商品是否存在
        cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return {
                'success': False,
                'message': '商品不存在'
            }

        # 将关联图片的product_id设为NULL
        cursor.execute("UPDATE images SET product_id = NULL WHERE product_id = ?", (product_id,))

        # 删除商品
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

        conn.commit()
        conn.close()

        print(f"✅ 成功删除商品: {product[0]} (ID: {product_id})")
        return {
            'success': True,
            'message': '商品删除成功'
        }

    except Exception as e:
        print(f"❌ 删除商品失败: {str(e)}")
        return {
            'success': False,
            'message': f'删除商品失败: {str(e)}'
        }

# ==================== 图片管理相关函数 ====================

def add_image(db_path: str = 'system.db', path: str = '', remark: str = '',
              status: int = 1, product_id: int = None) -> dict:
    """
    添加图片
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO images (path, remark, status, product_id)
            VALUES (?, ?, ?, ?)
        """, (path, remark, status, product_id))

        image_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ 成功添加图片: {path} (ID: {image_id})")
        return {
            'success': True,
            'message': '图片添加成功',
            'image_id': image_id
        }

    except Exception as e:
        print(f"❌ 添加图片失败: {str(e)}")
        return {
            'success': False,
            'message': f'添加图片失败: {str(e)}'
        }

def query_images(db_path: str = 'system.db', page: int = 1, page_size: int = 20,
                 product_id: int = None, status: int = None) -> dict:
    """
    查询图片列表（分页，支持按商品ID和状态筛选）
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 构建查询条件
        where_conditions = []
        params = []

        if product_id is not None:
            where_conditions.append("i.product_id = ?")
            params.append(product_id)

        if status is not None:
            where_conditions.append("i.status = ?")
            params.append(status)

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM images i {where_clause}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # 分页查询（关联商品表获取商品名称）
        offset = (page - 1) * page_size
        data_sql = f"""
            SELECT i.*, p.name as product_name
            FROM images i
            LEFT JOIN products p ON i.product_id = p.id
            {where_clause}
            ORDER BY i.create_time DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, params + [page_size, offset])
        images = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'success': True,
            'data': images,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }

    except Exception as e:
        print(f"❌ 查询图片失败: {str(e)}")
        return {
            'success': False,
            'message': f'查询图片失败: {str(e)}',
            'data': [],
            'total': 0
        }

def update_image(db_path: str = 'system.db', image_id: int = 0,
                 path: str = '', remark: str = '', status: int = 1,
                 product_id: int = None) -> dict:
    """
    更新图片信息
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE images
            SET path = ?, remark = ?, status = ?, product_id = ?
            WHERE id = ?
        """, (path, remark, status, product_id, image_id))

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            print(f"✅ 成功更新图片: ID={image_id}")
            return {
                'success': True,
                'message': '图片更新成功'
            }
        else:
            conn.close()
            return {
                'success': False,
                'message': '图片不存在'
            }

    except Exception as e:
        print(f"❌ 更新图片失败: {str(e)}")
        return {
            'success': False,
            'message': f'更新图片失败: {str(e)}'
        }

def delete_image(db_path: str = 'system.db', image_id: int = 0) -> dict:
    """
    删除图片
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 先获取图片信息
        cursor.execute("SELECT path FROM images WHERE id = ?", (image_id,))
        image = cursor.fetchone()

        if not image:
            conn.close()
            return {
                'success': False,
                'message': '图片不存在'
            }

        # 删除图片记录
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))

        conn.commit()
        conn.close()

        print(f"✅ 成功删除图片: {image[0]} (ID: {image_id})")
        return {
            'success': True,
            'message': '图片删除成功'
        }

    except Exception as e:
        print(f"❌ 删除图片失败: {str(e)}")
        return {
            'success': False,
            'message': f'删除图片失败: {str(e)}'
        }

def get_product_images(db_path: str = 'system.db', product_id: int = 0) -> list:
    """
    获取指定商品的所有图片
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM images
            WHERE product_id = ? AND status = 1
            ORDER BY create_time DESC
        """, (product_id,))

        images = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return images

    except Exception as e:
        print(f"❌ 获取商品图片失败: {str(e)}")
        return []

def get_product_with_images(db_path: str = 'system.db', product_id: int = 0) -> dict:
    """
    获取商品信息及其关联的所有图片
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取商品信息
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return {
                'success': False,
                'message': '商品不存在'
            }

        # 获取关联图片
        cursor.execute("""
            SELECT * FROM images
            WHERE product_id = ? AND status = 1
            ORDER BY create_time DESC
        """, (product_id,))

        images = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            'success': True,
            'product': dict(product),
            'images': images
        }

    except Exception as e:
        print(f"❌ 获取商品详情失败: {str(e)}")
        return {
            'success': False,
            'message': f'获取商品详情失败: {str(e)}'
        }

def get_all_products_simple(db_path: str = 'system.db') -> list:
    """
    获取所有商品的简单信息（用于下拉选择）
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM products ORDER BY name ASC")
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return products

    except Exception as e:
        print(f"❌ 获取商品列表失败: {str(e)}")
        return []
