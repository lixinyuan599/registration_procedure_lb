"""
数据库迁移: 给 doctors 表添加 invite_code 列，并为已有医生生成邀请码
"""

import sqlite3
import secrets


def generate_code():
    return secrets.token_hex(4).upper()


def main():
    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(doctors)")
    columns = [row[1] for row in cursor.fetchall()]

    if "invite_code" not in columns:
        print("添加 invite_code 列...")
        cursor.execute("ALTER TABLE doctors ADD COLUMN invite_code VARCHAR(16)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_doctors_invite_code ON doctors(invite_code)")
        conn.commit()
        print("invite_code 列已添加")
    else:
        print("invite_code 列已存在，跳过")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_doctors_invite_code ON doctors(invite_code)")
        conn.commit()

    # 为没有邀请码的医生生成邀请码
    cursor.execute("SELECT id, name FROM doctors WHERE invite_code IS NULL OR invite_code = ''")
    doctors = cursor.fetchall()

    if doctors:
        print(f"\n为 {len(doctors)} 位医生生成邀请码:")
        for doc_id, name in doctors:
            code = generate_code()
            cursor.execute("UPDATE doctors SET invite_code = ? WHERE id = ?", (code, doc_id))
            print(f"  医生 {name} (ID={doc_id}): 邀请码 = {code}")
        conn.commit()
    else:
        print("所有医生已有邀请码")

    # 显示所有医生的邀请码
    print("\n当前所有医生邀请码:")
    print("-" * 50)
    cursor.execute("SELECT id, name, invite_code FROM doctors ORDER BY id")
    for doc_id, name, code in cursor.fetchall():
        print(f"  ID={doc_id}  {name:>10s}  邀请码: {code}")
    print("-" * 50)

    conn.close()
    print("\n迁移完成!")


if __name__ == "__main__":
    main()
