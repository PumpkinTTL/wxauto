from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time

# 全局调度器实例
scheduler = BackgroundScheduler()

def print_time(task_name, custom_message=None):
    """
    打印时间的任务函数
    
    参数:
        task_name: 任务名称
        custom_message: 自定义消息(可选)
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if custom_message:
        print(f"[{current_time}] 任务 '{task_name}': {custom_message}")
    else:
        print(f"[{current_time}] 任务 '{task_name}' 执行")

def add_print_time_task(task_name, run_time, custom_message=None):
    """
    添加打印时间的任务
    
    参数:
        task_name: 任务名称(也作为任务ID)
        run_time: 任务执行时间(datetime对象或字符串)
        custom_message: 自定义消息(可选)
    """
    print(f"添加打印时间任务: {task_name}")
    
    # 添加任务到调度器
    scheduler.add_job(
        print_time,
        'date',
        run_date=run_time,
        id=task_name,
        args=[task_name],
        kwargs={'custom_message': custom_message}
    )
    
    # 如果调度器未启动，则启动它
    if not scheduler.running:
        scheduler.start()
        print("调度器已启动")

# 使用示例
if __name__ == '__main__':
    # 添加多个打印时间的任务
    add_print_time_task(
        task_name="早上任务",
        run_time=datetime.now() + timedelta(seconds=10),  # 10秒后执行
        custom_message="这是一条早上问候"
    )

    add_print_time_task(
        task_name="中午任务",
        run_time=datetime.now() + timedelta(seconds=20),  # 20秒后执行
        custom_message="午休时间提醒",
    )

    add_print_time_task(
        task_name="晚上任务",
        run_time=datetime.now() + timedelta(seconds=30),  # 30秒后执行
        custom_message="下班时间提醒"
    )

    # 添加一个未来特定时间的任务
    add_print_time_task(
        task_name="特定日期任务",
        run_time="2025-09-01 10:00:00",  # 可以接受字符串格式的时间
        custom_message="这是一个未来日期的任务"
    )

    print("主程序继续运行，等待任务执行...")

    try:
        # 保持主程序运行
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("调度器已关闭")
