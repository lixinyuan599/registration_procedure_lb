"""
迁移脚本：给 appointments 表添加 queue_number 列
"""
import sqlite3

DB_PATH = "clinic.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(appointments)")
    columns = [col[1] for col in cursor.fetchall()]

    if "queue_number" not in columns:
        print("添加 queue_number 列...")
        cursor.execute("ALTER TABLE appointments ADD COLUMN queue_number INTEGER DEFAULT 0")
        conn.commit()
        print("queue_number 列已添加")

        print("为已有预约生成排队号...")
        cursor.execute("""
            SELECT id, schedule_id FROM appointments
            WHERE status != 'cancelled'
            ORDER BY schedule_id, created_at
        """)
        rows = cursor.fetchall()

        schedule_counter = {}
        for apt_id, schedule_id in rows:
            schedule_counter[schedule_id] = schedule_counter.get(schedule_id, 0) + 1
            cursor.execute(
                "UPDATE appointments SET queue_number = ? WHERE id = ?",
                (schedule_counter[schedule_id], apt_id)
            )

        conn.commit()
        print(f"已为 {len(rows)} 条预约生成排队号")
    else:
        print("queue_number 列已存在，跳过")

    conn.close()
    print("迁移完成!")


if __name__ == "__main__":
    migrate()
