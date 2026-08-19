"""Minecraft 待發道具佇列。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import BRANCH_C_PENDING_DELIVERIES_TABLE


@db_transaction
def add_pending_delivery(cursor, user_account, mc_item_id, quantity, order_id):
    cursor.execute(f"""
        INSERT INTO `{BRANCH_C_PENDING_DELIVERIES_TABLE}`
        (user_account, mc_item_id, quantity, order_id)
        VALUES (%s, %s, %s, %s)
    """, (user_account, mc_item_id, quantity, order_id))


@db_transaction
def get_all_pending_deliveries(cursor):
    cursor.execute(f"SELECT * FROM `{BRANCH_C_PENDING_DELIVERIES_TABLE}` ORDER BY created_at ASC")
    return cursor.fetchall()


@db_transaction
def delete_pending_delivery(cursor, delivery_id):
    cursor.execute(f"DELETE FROM `{BRANCH_C_PENDING_DELIVERIES_TABLE}` WHERE id = %s", (delivery_id,))
