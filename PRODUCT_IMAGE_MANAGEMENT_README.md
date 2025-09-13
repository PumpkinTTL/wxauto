# 📦 商品和图片管理功能

## 🎯 功能概述

为智能办公系统新增了商品管理和图片管理功能，专门用于支持自动化图像识别任务。这两个模块可以帮助用户管理商品信息和相关的识别图片，为后续的自动化操作提供数据支持。

## 🗄️ 数据库设计

### 商品表 (products)
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 商品ID
    name TEXT NOT NULL,                    -- 商品名称
    cover TEXT,                            -- 商品封面图片路径
    price DECIMAL(10,2) DEFAULT 0.00,     -- 商品价格
    create_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')), -- 创建时间
    remark TEXT                            -- 备注信息
);
```

### 图片表 (images)
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 图片ID
    create_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')), -- 创建时间
    remark TEXT,                           -- 备注信息
    status INTEGER DEFAULT 1,             -- 状态：0-禁用，1-启用
    path TEXT NOT NULL,                    -- 图片路径
    product_id INTEGER,                    -- 关联商品ID（可选）
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);
```

## 🔧 API接口

### 商品管理API
- `add_product_api(product_data)` - 添加商品
- `query_products_api(query_params)` - 查询商品列表（支持分页和搜索）
- `update_product_api(product_data)` - 更新商品信息
- `delete_product_api(product_id)` - 删除商品
- `get_products_simple_api()` - 获取商品简单列表（用于下拉选择）

### 图片管理API
- `add_image_api(image_data)` - 添加图片
- `query_images_api(query_params)` - 查询图片列表（支持分页和筛选）
- `update_image_api(image_data)` - 更新图片信息
- `delete_image_api(image_id)` - 删除图片
- `get_product_images_api(product_id)` - 获取商品关联图片

## 🎨 前端界面

### 商品管理界面 (`product_management.html`)
- **功能特点**：
  - 商品列表展示（支持分页）
  - 商品搜索（按名称）
  - 添加/编辑商品对话框
  - 商品封面图片预览
  - 价格格式化显示
  - 响应式设计

- **操作流程**：
  1. 点击"添加商品"按钮创建新商品
  2. 填写商品名称、封面URL、价格和备注
  3. 在列表中可以编辑或删除商品
  4. 支持按商品名称搜索

### 图片管理界面 (`image_management.html`)
- **功能特点**：
  - 图片列表展示（支持分页）
  - 图片预览功能
  - 商品关联筛选
  - 状态筛选（启用/禁用）
  - 添加/编辑图片对话框
  - 响应式设计

- **操作流程**：
  1. 点击"添加图片"按钮创建新图片记录
  2. 输入图片路径/URL
  3. 选择关联商品（可选）
  4. 设置状态和备注信息
  5. 可以按商品或状态筛选图片
  6. 点击图片可以预览

## 🚀 使用方法

### 1. 启动应用程序
```bash
python main.py
```

### 2. 访问功能模块
在主界面左侧菜单中找到"自动化管理"分组：
- 📦 商品管理
- 🖼️ 图片管理

### 3. 基本操作流程

#### 商品管理流程：
1. 进入商品管理页面
2. 点击"添加商品"创建商品
3. 填写商品信息并保存
4. 可以随时编辑或删除商品

#### 图片管理流程：
1. 进入图片管理页面
2. 点击"添加图片"创建图片记录
3. 输入图片路径并选择关联商品
4. 可以按商品筛选查看相关图片
5. 点击图片可以预览

## 💡 设计特点

### 1. 灵活的关联关系
- 图片可以关联商品，也可以不关联（用于通用识别）
- 删除商品时，关联图片不会被删除，只是解除关联关系

### 2. 状态管理
- 图片支持启用/禁用状态控制
- 便于管理哪些图片用于识别

### 3. 搜索和筛选
- 商品支持按名称搜索
- 图片支持按商品和状态筛选
- 所有列表都支持分页显示

### 4. 用户体验
- 现代化的UI设计
- 响应式布局适配不同屏幕
- 图片预览功能
- 友好的错误提示和确认对话框

## 🔮 扩展可能性

### 1. 图像识别集成
- 可以基于商品关联的图片进行自动化识别
- 支持多图片匹配提高识别准确率

### 2. 批量操作
- 批量上传图片
- 批量关联商品
- 批量状态修改

### 3. 图片管理增强
- 本地图片上传
- 图片压缩和优化
- 图片标签和分类

### 4. 数据导入导出
- Excel批量导入商品
- 图片信息导出
- 数据备份和恢复

## 📊 技术实现

### 后端技术栈
- **数据库**: SQLite3 (轻量级，无需额外配置)
- **API层**: Python函数式API设计
- **数据处理**: 支持分页、搜索、筛选
- **关联查询**: 外键关联，支持联表查询

### 前端技术栈
- **框架**: Vue 3 + Element Plus
- **样式**: CSS3 + Animate.css动画
- **图标**: Element Plus Icons
- **响应式**: 移动端适配

### 特色功能
- **实时预览**: 图片点击预览
- **表单验证**: 完整的输入验证
- **错误处理**: 友好的错误提示
- **加载状态**: 操作过程中的加载提示

## 🎉 总结

商品和图片管理功能为智能办公系统增加了强大的数据管理能力，为后续的自动化图像识别功能奠定了基础。通过直观的界面和完善的API，用户可以轻松管理商品信息和识别图片，提高自动化操作的准确性和效率。
