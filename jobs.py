from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import time

def job1():
    print(f'任务1执行')
    for i in range(50):
        print(f'任务====1====执行第{i}次')
        if i == 10:
            print(f'10次运行,中断退出')
            create_job_delta(job1, 5)
            return
        time.sleep(1)
    

def job2():
    print(f'任务2执行')
    for i in range(50):
        print(f'任务=====2====执行第{i}次')
        time.sleep(1)
# 创建延时任务
def create_job_delta(task_func,_timedelta=5):
    print(f'任务{task_func.__name__}中断,开始重新创建任务')
    scheduler = BackgroundScheduler()
    # 设置5分钟后执行
    run_time = datetime.now() + timedelta(seconds=_timedelta)
    scheduler.add_job(
        func=task_func,
        trigger='date',
        run_date=run_time,
        id=f'{task_func.__name__}_job'  # 用函数名作为ID前缀
    )
    scheduler.start()
    stop_job(scheduler,'job1')
    return scheduler  # 返回调度器以便后续控制

# 根据id停止任务
def stop_task(sd,id):
    sd.remove_job(id)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=job1, trigger='date', run_date=datetime(2025, 8,29, 14, 12,0),id='job1')
    scheduler.add_job(func=job2, trigger='date', run_date=datetime(2025, 8,29, 14, 12,5),id='job2')
    scheduler.start()
    for i in range(100):
        print(f'阻塞{i}次')
        time.sleep(2)