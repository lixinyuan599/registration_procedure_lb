"""
迁移脚本：给 tenants 表添加 subtitle 列
"""
import sqlite3

DB_PATH = "clinic.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(tenants)")
    columns = [col[1] for col in cursor.fetchall()]

    if "subtitle" not in columns:
        print("添加 subtitle 列...")
        cursor.execute("ALTER TABLE tenants ADD COLUMN subtitle VARCHAR(256)")
        conn.commit()
        print("subtitle 列已添加")
    else:
        print("subtitle 列已存在，跳过")

    conn.close()
    print("迁移完成!")


if __name__ == "__main__":
    migrate()
