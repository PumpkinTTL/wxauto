# 直播间数据查询功能使用说明

## 📝 功能概述

当直播间正确打开没有错误时，系统会自动查询该直播间绑定的商品和商品图片信息以及话术，并在原有操作弹幕的基础上打印出来。

## 🎯 主要特性

### ✨ 自动化数据查询
- 📦 **商品信息**: 查询直播间绑定的商品（名称、价格、封面、备注）
- 🖼️ **商品图片**: 查询商品关联的所有图片（路径、备注）
- 💬 **话术信息**: 查询直播间绑定的话术内容

### 🔄 无缝集成
- 在直播间成功打开后自动触发
- 不影响原有的弹幕操作流程
- 支持测试模式和正常模式

## 📊 数据库结构

### 表关联关系
```
rooms (直播间表)
  ↓ product_id
products (商品表)
  ↓ product_id
images (图片表)

rooms (直播间表)
  ↓ room_id
room_speeches (关联表)
  ↓ speech_id
speech (话术表)
```

### 主要字段
- **rooms**: id, name, product_id
- **products**: id, name, cover, price, remark
- **images**: id, path, remark, product_id
- **speech**: id, content, create_time
- **room_speeches**: room_id, speech_id, status

## 🚀 使用方法

### 1. 数据配置（推荐）

#### 绑定商品到直播间
```sql
UPDATE rooms SET product_id = 商品ID WHERE id = 直播间ID;
```

#### 为商品添加图片
```sql
INSERT INTO images (path, remark, product_id) 
VALUES ('图片路径', '图片说明', 商品ID);
```

#### 为直播间绑定话术
```sql
INSERT INTO room_speeches (room_id, speech_id, create_time, status)
VALUES (直播间ID, 话术ID, '2025-08-29 20:00:00', 1);
```

### 2. 执行跟播任务

通过任务管理器创建跟播任务，或手动调用：

```python
from task_manager import execute_single_room_follow

# 执行跟播（会自动查询和打印数据）
success = execute_single_room_follow(
    room_id=72,
    room_name="哈利路亚",
    test_mode=False
)
```

### 3. 查看输出结果

当直播间成功打开后，控制台会显示类似输出：

```
============================================================
📺 直播间 72 数据装配完成
============================================================
💰 绑定商品:
   名称: 超值好物牙膏套装
   价格: ¥89.99
   封面: product_cover.jpg
   备注: 温和配方，适合全家使用

🖼️ 商品图片: (2 张)
   1. /images/product1.jpg
      备注: 产品主图
   2. /images/product2.jpg
      备注: 使用场景

💬 绑定话术: (3 条)
   1. 欢迎大家来到直播间！
   2. 这款产品质量很好，推荐购买
   3. 有问题可以随时咨询哦～
============================================================
```

## 📁 相关文件

### 核心文件
- **`room_data_query.py`**: 数据查询工具模块
- **`follwRoom.py`**: 直播间操作主程序（已集成）
- **`task_manager.py`**: 任务管理器（调用入口）

### 测试文件
- **`test_room_data_query.py`**: 功能测试脚本
- **`demo_room_data_query.py`**: 功能演示说明

## 🔧 API 参考

### 主要函数

#### `get_room_product_info(room_id)`
查询直播间绑定的商品信息
- **参数**: room_id (int) - 直播间ID
- **返回**: 商品信息字典或None

#### `get_product_images(product_id)`
查询商品关联的图片列表
- **参数**: product_id (int) - 商品ID
- **返回**: 图片信息列表

#### `get_room_speeches(room_id)`
查询直播间绑定的话术列表
- **参数**: room_id (int) - 直播间ID
- **返回**: 话术信息列表

#### `get_room_complete_data(room_id)`
一次性查询所有相关数据
- **参数**: room_id (int) - 直播间ID
- **返回**: 完整数据字典

#### `query_and_print_room_data(room_id, room_name)`
查询并打印直播间数据（集成函数）
- **参数**: 
  - room_id (int) - 直播间ID
  - room_name (str) - 直播间名称
- **返回**: 查询到的数据字典

## ⚠️ 注意事项

1. **数据配置**: 商品、图片、话术绑定是可选的，没有绑定时会给出相应提示
2. **性能**: 查询使用联表操作，建议合理配置数据量
3. **错误处理**: 所有查询都有异常捕获，不会影响正常的跟播流程
4. **测试**: 建议先使用 `test_room_data_query.py` 验证功能

## 📈 扩展建议

1. **缓存机制**: 可以添加数据缓存提高查询效率
2. **更多数据类型**: 支持视频、音频等媒体文件
3. **自定义格式**: 支持用户自定义输出格式
4. **数据导出**: 支持将查询结果导出到文件

## 🆘 故障排除

### 常见问题

**Q: 查询不到数据？**
A: 检查直播间是否正确绑定了商品和话术

**Q: 输出格式乱码？**
A: 确保控制台支持UTF-8编码

**Q: 查询速度慢？**
A: 检查数据库索引是否正确创建

### 调试方法

1. 运行测试脚本验证功能：
   ```bash
   python test_room_data_query.py
   ```

2. 检查数据库数据：
   ```sql
   -- 检查直播间信息
   SELECT * FROM rooms WHERE id = 直播间ID;
   
   -- 检查商品绑定
   SELECT r.name, p.name as product_name 
   FROM rooms r 
   LEFT JOIN products p ON r.product_id = p.id 
   WHERE r.id = 直播间ID;
   
   -- 检查话术绑定
   SELECT COUNT(*) FROM room_speeches WHERE room_id = 直播间ID;
   ```

## 🎉 版本信息

- **版本**: v1.0.0
- **创建日期**: 2025-08-29
- **作者**: Qoder AI Assistant
- **更新记录**: 
  - v1.0.0 - 初始版本，支持商品、图片、话术查询