import sqlite3

conn = sqlite3.connect('system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== 直播间列表 ===")
cursor.execute('SELECT id, name, status FROM rooms LIMIT 10')
rooms = cursor.fetchall()

if rooms:
    for room in rooms:
        print(f"ID: {room['id']}, 名称: {room['name']}, 状态: {room['status']}")
else:
    print("数据库中没有直播间数据")

conn.close()