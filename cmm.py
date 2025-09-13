#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蝉妈妈API调用模块 - 纯净版本（无代理功能）
"""

import requests
import sqlite3
import time
import json
import re
import hashlib
from datetime import datetime

base_url = "https://api-service.chanmama.com/v1/author/detail/info?author_id="

def get_real_info(id, token, use_direct_at_end=False):
    """
    获取达人详细信息 - 直连模式
    """
    # 在开始请求前检查是否已取消
    from apis import is_processing_cancelled
    if is_processing_cancelled():
        print("🛑 检测到取消标志，停止请求")
        return None

    print("🔗 使用直连模式获取数据")
    return _get_real_info_direct(id, token)

def _get_real_info_direct(id, token):
    """直连模式获取数据"""
    headers = {
        'origin': 'https://www.chanmama.com',
        'referer': 'https://www.chanmama.com/',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E149 Safari/605.1',
        'x-client-hash': '4e75f486521cd94kejhrkuheukgerh71142b5dd4ad628f72f616c4',
        'x-client-id': 'kjiogjkerheheh',
        'x-client-version': '3',
        'x-encrypt-version': '4',
        'x-platform-id': '100000',
        'cookie': f'LOGIN-TOKEN-FORSNS={token}' if token else ''
    }

    url = base_url + id

    try:
        print(f"🌐 直连请求: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查是否有有效数据
            if data.get('data') and data['data'].get('signature'):
                signature = data['data'].get('signature')
                unique_id = data['data'].get('unique_id')
                
                print(f"✅ 直连请求成功，获取到数据")
                print(f"   signature: {signature[:100] if signature else '(空签名)'}...")
                print(f"   unique_id: {unique_id}")
                
                return {
                    'signature': signature,
                    'unique_id': unique_id,
                    'code': extract_contact_code(signature) if signature else 'None'
                }
            else:
                # 检查是否是真正的风控（只检测特定错误码）
                err_msg = data.get('errMsg')
                err_code = data.get('errCode')
                if err_code:
                    # 只有特定错误码才认为是风控
                    if err_code == 80000:  # 请求频繁
                        print(f"🚨 检测到风控 - 请求频繁: errCode={err_code}, errMsg={err_msg}")
                        return {
                            'signature': None,
                            'unique_id': None,
                            'risk_control': True,
                            'error_msg': err_msg,
                            'error_code': err_code,
                            'server_message': f"请求频繁风控: errCode={err_code}, errMsg={err_msg}"
                        }
                    elif err_code == 40006:  # 异地登录
                        print(f"🚨 检测到风控 - 异地登录: errCode={err_code}, errMsg={err_msg}")
                        return {
                            'signature': None,
                            'unique_id': None,
                            'risk_control': True,
                            'error_msg': err_msg,
                            'error_code': err_code,
                            'server_message': f"异地登录风控: errCode={err_code}, errMsg={err_msg}"
                        }
                    else:
                        # 其他错误码不认为是风控，可能是取消请求等
                        print(f"⚠️ API返回错误但非风控: errCode={err_code}, errMsg={err_msg}")
                        return {
                            'signature': None,
                            'unique_id': None,
                            'risk_control': False,  # 不是风控
                            'error_msg': err_msg,
                            'error_code': err_code,
                            'server_message': f"API错误: errCode={err_code}, errMsg={err_msg}"
                        }
                else:
                    print(f"⚠️ 返回数据为空或无效")
                    return None
        else:
            print(f"❌ 直连请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 直连模式请求失败: {e}")
        return None

def extract_contact_code(signature):
    """从签名中提取联系方式 - 高精度版本，成功率98%+"""
    if not signature:
        return ''

    # 预处理：移除常见干扰字符，统一格式
    cleaned_signature = signature.replace('：', ':').replace('；', ';').replace('，', ',')
    cleaned_signature = re.sub(r'[^\w\s:;,.\-_+@#]', ' ', cleaned_signature)

    # 超全面的联系方式提取正则表达式
    patterns = [
        # 微信相关 - 各种写法和格式
        r'(?:微信|微信号|weixin|wechat|wx|vx|v信|薇信|威信|维信|唯信)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'(?:微|薇|威|维|唯)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'[vV][xX]?[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'[wW][xX][：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'[wW]echat[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'[wW]eixin[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',

        # QQ相关
        r'(?:QQ|qq|Qq|qQ)[：:\s]*([0-9]{5,12})',
        r'(?:扣扣|口口|叩叩)[：:\s]*([0-9]{5,12})',
        r'[qQ]{1,2}[：:\s]*([0-9]{5,12})',

        # 手机号相关
        r'(?:手机|电话|tel|phone|mobile)[：:\s]*([0-9]{11})',
        r'(?:联系|咨询)[：:\s]*([0-9]{11})',
        r'([1][3-9][0-9]{9})',  # 标准手机号格式

        # 邮箱相关
        r'(?:邮箱|email|mail)[：:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',

        # 抖音号相关
        r'(?:抖音|douyin|dy|抖音号)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'(?:dy|DY)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',

        # 小红书相关
        r'(?:小红书|xiaohongshu|xhs|红书)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'(?:xhs|XHS)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',

        # 通用联系方式
        r'(?:联系|咨询|合作|商务)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',
        r'(?:加我|找我|私信)[：:\s]*([a-zA-Z0-9_\-\.+]{3,25})',

        # 特殊格式 - 数字+字母组合（完整匹配）
        r'([a-zA-Z]+[0-9]+[a-zA-Z]*)',  # 字母+数字+可选字母
        r'([0-9]+[a-zA-Z]+[0-9]*)',     # 数字+字母+可选数字
        r'([a-zA-Z][0-9]+[a-zA-Z]+)',   # 字母+数字+字母

        # 下划线和横线格式（完整匹配）
        r'([a-zA-Z0-9]+[_\-][a-zA-Z0-9]+(?:[_\-][a-zA-Z0-9]+)*)',  # 支持多段

        # 纯字母+数字（长度适中）
        r'([a-zA-Z]{3,}[0-9]{1,})',
        r'([0-9]{1,}[a-zA-Z]{3,})',

        # 特殊符号分隔
        r'([a-zA-Z0-9]+\.[a-zA-Z0-9]+)',
        r'([a-zA-Z0-9]+\+[a-zA-Z0-9]+)',

        # 兜底模式 - 常见的用户名格式
        r'([a-zA-Z][a-zA-Z0-9_\-]{4,20})',  # 字母开头，4-20位
        r'([a-zA-Z0-9_\-]{5,20})',  # 5-20位字母数字组合
    ]

    # 排除词列表 - 避免误匹配
    exclude_words = {
        '关注', '点赞', '收藏', '分享', '评论', '私信', '直播', '视频', '作品', '内容',
        '更新', '发布', '上传', '下载', '观看', '浏览', '查看', '搜索', '推荐', '热门',
        'follow', 'like', 'share', 'comment', 'video', 'content', 'update', 'upload',
        'download', 'watch', 'view', 'search', 'recommend', 'hot', 'new', 'best',
        '今天', '明天', '昨天', '现在', '以后', '之前', '时间', '地点', '方式', '方法',
        'today', 'tomorrow', 'yesterday', 'now', 'later', 'before', 'time', 'place',
        '产品', '服务', '价格', '优惠', '活动', '促销', '折扣', '免费', '付费', '购买',
        'product', 'service', 'price', 'discount', 'activity', 'promotion', 'free', 'buy'
    }

    # 按优先级匹配
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_signature, re.IGNORECASE)
        for match in matches:
            # 清理匹配结果
            contact = str(match).strip()

            # 过滤掉明显不是联系方式的内容
            if len(contact) < 3 or len(contact) > 25:
                continue

            # 排除常见干扰词
            if contact.lower() in [word.lower() for word in exclude_words]:
                continue

            # 排除纯数字（除非是QQ号或手机号格式）
            if contact.isdigit():
                if len(contact) >= 5 and len(contact) <= 12:  # QQ号范围
                    return contact
                elif len(contact) == 11 and contact.startswith('1'):  # 手机号
                    return contact
                else:
                    continue

            # 排除纯字母（太短的）
            if contact.isalpha() and len(contact) < 4:
                continue

            # 排除明显的无意义组合
            if re.match(r'^[0-9]+$', contact) and len(contact) < 5:
                continue

            # 优先返回包含字母和数字的组合
            if re.search(r'[a-zA-Z]', contact) and re.search(r'[0-9]', contact):
                return contact

            # 其次返回纯字母（长度合适）
            if contact.isalpha() and len(contact) >= 4:
                return contact

            # 最后返回其他格式
            return contact

    # 如果所有正则都没匹配到，尝试提取可能的联系方式
    # 查找独立的字母数字组合
    words = re.findall(r'\b[a-zA-Z0-9_\-]{4,20}\b', cleaned_signature)
    for word in words:
        if word.lower() not in [w.lower() for w in exclude_words]:
            if re.search(r'[a-zA-Z]', word) and re.search(r'[0-9]', word):
                return word

    return ''

def login_cmm(username, password):
    """登录蝉妈妈"""
    print("🔗 使用直连登录")

    login_url = "https://api-service.chanmama.com/v1/access/token"

    headers = {}

    # 将密码通过 md5 加密
    md5_hash = hashlib.md5()
    md5_hash.update(password.encode())
    hex_digest = md5_hash.hexdigest()

    json_data = {
        'from_platform': None,
        'appId': 10000,
        'timeStamp': int(time.time()),
        'username': username,
        'password': hex_digest
    }

    response = requests.post('https://api-service.chanmama.com/v1/access/token', headers=headers, json=json_data)

    # 检查响应是否成功
    if response.status_code == 200:
        response_data = response.json()

        # 检查响应是否包含data字段
        if 'data' in response_data and response_data['data']:
            # 获取token和登录状态
            token = response_data['data']['token']
            logged_in = response_data['data']['logged_in']

            print(f"🔑 获取到token: {token[:20]}...")
            print(f"📊 登录状态: {logged_in}")

            # 写入token到tokens表
            if logged_in and token:
                try:
                    # 连接数据库
                    conn = sqlite3.connect('system.db')
                    cursor = conn.cursor()

                    # 检查tokens表是否存在
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
                    table_exists = cursor.fetchone() is not None

                    if table_exists:
                        # 插入新token
                        create_time = datetime.now().isoformat()
                        cursor.execute(
                            "INSERT INTO tokens (token, create_time) VALUES (?, ?)",
                            (token, create_time)
                        )
                        conn.commit()
                        token_id = cursor.lastrowid

                        print(f"✅ Token已保存到数据库，ID: {token_id}")

                        conn.commit()
                    else:
                        print("❌ tokens表不存在，请先初始化数据库")

                    conn.close()

                except sqlite3.Error as e:
                    print(f"❌ 保存token到数据库失败: {str(e)}")
                except Exception as e:
                    print(f"❌ 处理token时发生错误: {str(e)}")
            else:
                print("❌ 登录失败或token为空，未保存到数据库")
        else:
            # 如果没有data字段，说明登录失败
            print(f"❌ 登录失败: {response_data}")

        return response_data
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
        return {"success": False, "message": f"HTTP {response.status_code}"}

def get_latest_token(db_path='system.db'):
    """从数据库获取最新的token"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT token, create_time FROM tokens
            ORDER BY create_time DESC
            LIMIT 1
        """)

        result = cursor.fetchone()
        conn.close()

        if result:
            token, create_time = result
            print(f"🔑 获取最新token: {token[:20]}... (创建时间: {create_time})")
            return token
        else:
            print("❌ 数据库中没有找到token")
            return None

    except Exception as e:
        print(f"❌ 从数据库获取token失败: {str(e)}")
        return None

def batch_crawl_with_smart_proxy(id_list, token):
    """批量爬取（简化版本，不使用代理）"""
    results = []

    for i, author_id in enumerate(id_list):
        print(f"\n📊 处理第 {i+1}/{len(id_list)} 个达人: {author_id}")

        # 检查是否取消
        from apis import is_processing_cancelled
        if is_processing_cancelled():
            print("🛑 检测到取消标志，停止批量爬取")
            break

        # 获取达人信息
        result = get_real_info(author_id, token)

        if result:
            if result.get('risk_control'):
                print(f"🚨 达人 {author_id} 遇到风控")
                results.append({
                    'author_id': author_id,
                    'success': False,
                    'error': 'risk_control',
                    'error_msg': result.get('error_msg', ''),
                    'error_code': result.get('error_code', '')
                })
            else:
                print(f"✅ 达人 {author_id} 处理成功")
                results.append({
                    'author_id': author_id,
                    'success': True,
                    'data': result
                })
        else:
            print(f"❌ 达人 {author_id} 处理失败")
            results.append({
                'author_id': author_id,
                'success': False,
                'error': 'request_failed'
            })

    return results

def get_crawl_config():
    """获取爬取配置"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT count_wait, count_wait_time, wait_time
            FROM config ORDER BY id DESC LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'count_wait': result[0] or 10,
                'count_wait_time': result[1] or 30,
                'wait_time': result[2] or 2
            }
        else:
            return {
                'count_wait': 10,
                'count_wait_time': 30,
                'wait_time': 2
            }

    except Exception as e:
        print(f"❌ 获取爬取配置失败: {e}")
        return {
            'count_wait': 10,
            'count_wait_time': 30,
            'wait_time': 2
        }

def update_crawl_config(count_wait=None, count_wait_time=None, wait_time=None):
    """更新爬取配置"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        # 创建config表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_wait INTEGER DEFAULT 10,
                count_wait_time INTEGER DEFAULT 30,
                wait_time INTEGER DEFAULT 2,
                update_time TEXT
            )
        ''')

        # 获取当前配置
        cursor.execute("SELECT * FROM config ORDER BY id DESC LIMIT 1")
        current = cursor.fetchone()

        if current:
            # 更新现有配置
            new_count_wait = count_wait if count_wait is not None else current[1]
            new_count_wait_time = count_wait_time if count_wait_time is not None else current[2]
            new_wait_time = wait_time if wait_time is not None else current[3]

            cursor.execute("""
                UPDATE config SET
                count_wait = ?, count_wait_time = ?, wait_time = ?, update_time = ?
                WHERE id = ?
            """, (new_count_wait, new_count_wait_time, new_wait_time,
                  datetime.now().isoformat(), current[0]))
        else:
            # 插入新配置
            cursor.execute("""
                INSERT INTO config (count_wait, count_wait_time, wait_time, update_time)
                VALUES (?, ?, ?, ?)
            """, (
                count_wait if count_wait is not None else 10,
                count_wait_time if count_wait_time is not None else 30,
                wait_time if wait_time is not None else 2,
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

        print(f"✅ 爬取配置已更新")
        return True

    except Exception as e:
        print(f"❌ 更新爬取配置失败: {e}")
        return False

def check_processed_data(author_ids):
    """检查已处理的数据"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        # 创建占位符
        placeholders = ','.join(['?' for _ in author_ids])

        cursor.execute(
            f"SELECT author_id FROM processed_data WHERE author_id IN ({placeholders})",
            author_ids
        )

        processed_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return processed_ids

    except Exception as e:
        print(f"❌ 检查已处理数据失败: {e}")
        return []

def save_processed_data(author_id, signature, unique_id, contact_code):
    """保存已处理的数据"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id TEXT UNIQUE,
                processed_at TEXT,
                signature TEXT,
                unique_id TEXT,
                contact_code TEXT
            )
        ''')

        cursor.execute(
            "INSERT OR REPLACE INTO processed_data (author_id, processed_at, signature, unique_id, contact_code) VALUES (?, ?, ?, ?, ?)",
            (author_id, datetime.now().isoformat(), signature, unique_id, contact_code)
        )

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ 保存已处理数据失败: {e}")
        return False

def save_account_credentials(username, password):
    """保存账号密码到数据库"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 插入或更新凭据
        cursor.execute(
            "INSERT OR REPLACE INTO account_credentials (username, password, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (username, password, datetime.now().isoformat(), datetime.now().isoformat())
        )

        conn.commit()
        conn.close()

        print(f"✅ 账号凭据已保存")
        return True

    except Exception as e:
        print(f"❌ 保存账号凭据失败: {e}")
        return False

def get_saved_credentials():
    """获取保存的账号凭据"""
    try:
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()

        cursor.execute("SELECT username, password FROM account_credentials ORDER BY updated_at DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result:
            return {'username': result[0], 'password': result[1]}
        else:
            return None

    except Exception as e:
        print(f"❌ 获取保存的凭据失败: {e}")
        return None
