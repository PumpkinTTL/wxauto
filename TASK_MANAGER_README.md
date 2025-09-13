# 定时任务管理器使用说明

## 概述

本项目已成功集成了基于APScheduler的定时任务管理系统，用于替代前端定时器，实现更可靠的微信自动化跟播提醒功能。

## 主要功能

### 1. 自动任务管理
- ✅ 每次启动程序时自动加载数据库中的跟播任务
- ✅ 自动同步`time_of_live`表中的直播时间，创建对应的提醒任务
- ✅ 自动清理过期的任务

### 2. 定时提醒
- ✅ 在设定的直播时间发送Windows系统通知
- ✅ 通知内容包含直播间名称和备注信息
- ✅ 支持后台运行，不依赖前端界面

### 3. 数据库集成
- ✅ 新增`tasks`表用于存储任务信息
- ✅ 与现有的`rooms`和`time_of_live`表完全兼容
- ✅ 任务状态自动管理（有效/无效）

## 技术架构

### 核心组件
1. **TaskManager类** - 任务管理器主类
2. **APScheduler** - 后台任务调度器
3. **SQLAlchemy** - 任务持久化存储
4. **win10toast** - Windows系统通知

### 数据库表结构

#### tasks表
```sql
CREATE TABLE tasks (
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
```

## 使用方式

### 1. 前端操作
在微信跟播页面添加直播时间时，系统会：
1. 将时间保存到`time_of_live`表
2. 自动创建对应的定时任务
3. 在指定时间发送系统通知

### 2. API接口
新增的API接口：
- `get_active_tasks()` - 获取活跃任务列表
- `sync_tasks_with_live_times()` - 手动同步任务
- `cleanup_expired_tasks()` - 清理过期任务
- `remove_task(task_id)` - 移除指定任务

### 3. 自动化流程
```
启动程序 → 初始化任务管理器 → 加载现有任务 → 同步直播时间 → 清理过期任务
    ↓
运行中：监听任务执行 → 发送通知 → 自动清理已执行任务
    ↓
关闭程序 → 停止任务管理器 → 保存任务状态
```

## 优势对比

### 原前端定时器方案
- ❌ 依赖前端界面运行
- ❌ 页面切换或关闭会失效
- ❌ 浏览器刷新会丢失任务
- ❌ 不支持程序重启后恢复

### 新后端任务管理器方案
- ✅ 后台独立运行
- ✅ 不依赖前端界面状态
- ✅ 程序重启后自动恢复任务
- ✅ 任务持久化存储
- ✅ 更精确的时间控制
- ✅ 完整的任务生命周期管理

## 配置说明

### 依赖包
```
APScheduler>=3.11.0     # 定时任务调度器
SQLAlchemy>=2.0.0       # 数据库ORM（APScheduler依赖）
win10toast>=0.9         # Windows系统通知
```

### 日志文件
- `task_manager.log` - 任务管理器运行日志
- 包含任务创建、执行、错误等详细信息

## 故障排除

### 常见问题
1. **任务不执行**
   - 检查`task_manager.log`日志
   - 确认任务时间格式正确
   - 验证数据库连接正常

2. **通知不显示**
   - 确认win10toast已安装
   - 检查Windows通知设置
   - 查看日志中的错误信息

3. **任务重复创建**
   - 系统会自动检查重复任务
   - 相同时间和直播间的任务只会创建一次

### 调试方法
1. 查看`task_manager.log`日志文件
2. 使用API接口`get_active_tasks()`检查任务状态
3. 手动执行`sync_tasks_with_live_times()`同步任务

## 开发说明

### 扩展任务类型
要添加新的任务类型，需要：
1. 在`TaskManager`类中添加对应的方法
2. 创建全局执行函数（避免序列化问题）
3. 在`_load_existing_tasks`中添加加载逻辑

### 自定义通知
可以修改`send_live_notification`函数来：
- 自定义通知样式
- 添加声音提醒
- 集成其他通知方式

## 测试验证

系统已通过完整测试，包括：
- ✅ 任务创建和执行
- ✅ 数据库持久化
- ✅ 系统通知发送
- ✅ API接口功能
- ✅ 异常处理机制

测试结果显示所有功能正常工作，可以放心使用。
