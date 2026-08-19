"""後台操作日誌。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import BRANCH_D_MANAGE_LOG_TABLE


@db_transaction
def add_log(cursor, admin_account, action, product_id, product_name):
    # 新增一筆後台操作記錄
    cursor.execute(f"""
        INSERT INTO {BRANCH_D_MANAGE_LOG_TABLE}
        (admin_account, action, product_id, product_name)
        VALUES (%s, %s, %s, %s)
    """, (admin_account, action, product_id, product_name))


@db_transaction
def get_logs(cursor):
    # 取得所有後台操作記錄，依時間降冪排列
    cursor.execute(f"""
        SELECT * FROM {BRANCH_D_MANAGE_LOG_TABLE}
        ORDER BY created_at DESC
    """)
    return cursor.fetchall()


@db_transaction
def get_log_months(cursor):
    """
    取得 manage_log 中有紀錄的月份清單,以及每個月的筆數。
    回傳格式: [{"month": "2025-11", "log_count": 8}, ...]
    """
    cursor.execute(f"""
        SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month,
               COUNT(*) AS log_count
        FROM {BRANCH_D_MANAGE_LOG_TABLE}
        GROUP BY month
        ORDER BY month DESC
    """)
    return cursor.fetchall()


@db_transaction
def get_logs_by_month(cursor, month):
    """
    取得指定月份(格式 YYYY-MM)的所有日誌紀錄,依時間降冪排列。
    """
    cursor.execute(f"""
        SELECT created_at, admin_account, action, product_id, product_name
        FROM {BRANCH_D_MANAGE_LOG_TABLE}
        WHERE DATE_FORMAT(created_at, '%%Y-%%m') = %s
        ORDER BY created_at DESC
    """, (month,))
    return cursor.fetchall()
