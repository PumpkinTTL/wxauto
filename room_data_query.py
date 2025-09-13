#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播间数据查询工具
用于查询直播间绑定的商品、图片和话术信息
"""

import sqlite3
from typing import Dict, List, Optional
import os
import json


def get_room_product_info(room_id: int, db_path: str = 'system.db') -> Optional[Dict]:
    """
    查询直播间绑定的商品信息
    
    Args:
        room_id: 直播间ID
        db_path: 数据库路径
        
    Returns:
        dict: 商品信息字典，如果没有绑定商品则返回None
        {
            'id': 商品ID,
            'name': 商品名称,
            'cover': 商品封面,
            'price': 商品价格,
            'create_time': 创建时间,
            'remark': 备注
        }
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 联表查询直播间绑定的商品信息
        query = """
            SELECT p.id, p.name, p.cover, p.price, p.create_time, p.remark
            FROM rooms r
            LEFT JOIN products p ON r.product_id = p.id
            WHERE r.id = ? AND r.product_id IS NOT NULL
        """
        
        cursor.execute(query, (room_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            product_info = dict(result)
            print(f"✅ 查询到直播间 {room_id} 绑定的商品: {product_info['name']}")
            return product_info
        else:
            print(f"⚠️ 直播间 {room_id} 没有绑定商品")
            return None
            
    except Exception as e:
        print(f"❌ 查询直播间商品信息失败: {str(e)}")
        return None


def get_product_images(product_id: int, db_path: str = 'system.db') -> List[Dict]:
    """
    查询商品绑定的图片信息
    
    Args:
        product_id: 商品ID
        db_path: 数据库路径
        
    Returns:
        list: 图片信息列表
        [
            {
                'id': 图片ID,
                'path': 图片路径,
                'remark': 备注,
                'status': 状态,
                'create_time': 创建时间
            }
        ]
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询商品绑定的所有图片
        query = """
            SELECT id, path, remark, status, create_time
            FROM images
            WHERE product_id = ? AND status = 1
            ORDER BY create_time ASC
        """
        
        cursor.execute(query, (product_id,))
        results = cursor.fetchall()
        conn.close()
        
        images = [dict(row) for row in results]
        
        if images:
            print(f"✅ 查询到商品 {product_id} 绑定的 {len(images)} 张图片")
            for i, img in enumerate(images, 1):
                print(f"   {i}. {img['path']} ({img['remark'] or '无备注'})")
        else:
            print(f"⚠️ 商品 {product_id} 没有绑定图片")
            
        return images
        
    except Exception as e:
        print(f"❌ 查询商品图片信息失败: {str(e)}")
        return []


def get_room_speeches(room_id: int, db_path: str = 'system.db') -> List[Dict]:
    """
    查询直播间绑定的话术信息
    
    Args:
        room_id: 直播间ID
        db_path: 数据库路径
        
    Returns:
        list: 话术信息列表
        [
            {
                'id': 话术ID,
                'content': 话术内容,
                'create_time': 创建时间,
                'bind_time': 绑定时间
            }
        ]
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询直播间绑定的所有话术
        query = """
            SELECT s.id, s.content, s.create_time, rs.create_time as bind_time
            FROM room_speeches rs
            JOIN speech s ON rs.speech_id = s.id
            WHERE rs.room_id = ? AND rs.status = 1 AND s.status = 1
            ORDER BY rs.create_time ASC
        """
        
        cursor.execute(query, (room_id,))
        results = cursor.fetchall()
        conn.close()
        
        speeches = [dict(row) for row in results]
        
        if speeches:
            print(f"✅ 查询到直播间 {room_id} 绑定的 {len(speeches)} 条话术")
            for i, speech in enumerate(speeches, 1):
                content = speech['content']
                display_content = content[:30] + '...' if len(content) > 30 else content
                print(f"   {i}. {display_content}")
        else:
            print(f"⚠️ 直播间 {room_id} 没有绑定话术")
            
        return speeches
        
    except Exception as e:
        print(f"❌ 查询直播间话术信息失败: {str(e)}")
        return []


def get_room_complete_data(room_id: int, db_path: str = 'system.db') -> Dict:
    """
    查询直播间的完整数据（商品、图片、话术）
    
    Args:
        room_id: 直播间ID
        db_path: 数据库路径
        
    Returns:
        dict: 完整数据字典
        {
            'room_id': 直播间ID,
            'product': 商品信息 or None,
            'images': 图片列表,
            'speeches': 话术列表,
            'has_data': 是否有绑定数据
        }
    """
    try:
        print(f"\n🔍 开始查询直播间 {room_id} 的完整数据...")
        
        # 1. 查询商品信息
        product_info = get_room_product_info(room_id, db_path)
        
        # 2. 查询图片信息
        images = []
        if product_info:
            images = get_product_images(product_info['id'], db_path)
        
        # 3. 查询话术信息
        speeches = get_room_speeches(room_id, db_path)
        
        # 4. 汇总结果
        complete_data = {
            'room_id': room_id,
            'product': product_info,
            'images': images,
            'speeches': speeches,
            'has_data': bool(product_info or images or speeches)
        }
        
        print(f"\n📊 直播间 {room_id} 数据查询汇总:")
        print(f"   💰 商品信息: {'✅ 有' if product_info else '❌ 无'}")
        print(f"   🖼️ 商品图片: {'✅ 有' if images else '❌ 无'} ({len(images)} 张)")
        print(f"   💬 绑定话术: {'✅ 有' if speeches else '❌ 无'} ({len(speeches)} 条)")
        print(f"   📈 数据完整性: {'✅ 完整' if complete_data['has_data'] else '⚠️ 缺失'}")
        
        return complete_data
        
    except Exception as e:
        print(f"❌ 查询直播间完整数据失败: {str(e)}")
        return {
            'room_id': room_id,
            'product': None,
            'images': [],
            'speeches': [],
            'has_data': False
        }


def print_room_data_summary(room_data: Dict):
    """
    打印直播间数据汇总（格式化输出）
    
    Args:
        room_data: get_room_complete_data返回的数据字典
    """
    try:
        room_id = room_data['room_id']
        product = room_data['product']
        images = room_data['images']
        speeches = room_data['speeches']
        
        print(f"\n" + "="*60)
        print(f"📺 直播间 {room_id} 数据装配完成")
        print(f"="*60)
        
        # 商品信息
        if product:
            print(f"💰 绑定商品:")
            print(f"   名称: {product['name']}")
            print(f"   价格: ¥{product['price']}")
            print(f"   封面: {product['cover'] or '无'}")
            print(f"   备注: {product['remark'] or '无'}")
        else:
            print(f"💰 绑定商品: ❌ 无")
        
        # 图片信息
        print(f"\n🖼️ 商品图片: ({len(images)} 张)")
        if images:
            for i, img in enumerate(images, 1):
                print(f"   {i}. {img['path']}")
                if img['remark']:
                    print(f"      备注: {img['remark']}")
        else:
            print(f"   ❌ 无绑定图片")
        
        # 话术信息
        print(f"\n💬 绑定话术: ({len(speeches)} 条)")
        if speeches:
            for i, speech in enumerate(speeches, 1):
                content = speech['content']
                # 如果话术过长，只显示前50个字符
                display_content = content[:50] + '...' if len(content) > 50 else content
                print(f"   {i}. {display_content}")
        else:
            print(f"   ❌ 无绑定话术")
        
        print(f"="*60)
        
    except Exception as e:
        print(f"❌ 打印数据汇总失败: {str(e)}")


def check_data_availability(room_id: int, db_path: str = 'system.db') -> Dict[str, bool]:
    """
    检查直播间数据的可用性
    
    Args:
        room_id: 直播间ID
        db_path: 数据库路径
        
    Returns:
        dict: 可用性检查结果
        {
            'has_product': 是否有商品,
            'has_images': 是否有图片,
            'has_speeches': 是否有话术,
            'all_ready': 所有数据是否就绪
        }
    """
    try:
        product_info = get_room_product_info(room_id, db_path)
        
        images = []
        if product_info:
            images = get_product_images(product_info['id'], db_path)
        
        speeches = get_room_speeches(room_id, db_path)
        
        availability = {
            'has_product': bool(product_info),
            'has_images': bool(images),
            'has_speeches': bool(speeches),
            'all_ready': bool(product_info and images and speeches)
        }
        
        return availability
        
    except Exception as e:
        print(f"❌ 检查数据可用性失败: {str(e)}")
        return {
            'has_product': False,
            'has_images': False,
            'has_speeches': False,
            'all_ready': False
        }


if __name__ == "__main__":
    """测试数据查询功能"""
    print("🧪 测试直播间数据查询功能")
    print("=" * 60)
    
    # 测试直播间ID（假设存在）
    test_room_id = 72
    
    # 测试各个查询函数
    print(f"\n🔍 测试查询直播间 {test_room_id} 的数据...")
    
    # 测试完整数据查询
    room_data = get_room_complete_data(test_room_id)
    
    # 打印格式化汇总
    print_room_data_summary(room_data)
    
    # 测试可用性检查
    availability = check_data_availability(test_room_id)
    print(f"\n📋 数据可用性检查:")
    print(f"   商品: {'✅' if availability['has_product'] else '❌'}")
    print(f"   图片: {'✅' if availability['has_images'] else '❌'}")
    print(f"   话术: {'✅' if availability['has_speeches'] else '❌'}")
    print(f"   就绪: {'✅ 全部就绪' if availability['all_ready'] else '⚠️ 部分缺失'}")
    
    print(f"\n✨ 测试完成！")