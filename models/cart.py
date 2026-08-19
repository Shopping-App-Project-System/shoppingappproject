"""購物車。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import (
    BRANCH_A_TABLE,
    BRANCH_B_PRODUCTS_TABLE,
    BRANCH_B_PRODUCT_STOCK_TABLE,
    BRANCH_C_CART_TABLE,
)


@db_transaction
def get_cart_items(cursor, user_account):
    # 取得該會員的所有購物車商品，JOIN 商品表取得名稱、價格、圖片，JOIN 庫存表取得剩餘庫存
    cursor.execute(
        f'''SELECT c.id, c.user_id, c.product_id, c.quantity,
                    p.name, COALESCE(p.sale_price, p.original_price) AS price,
                    p.original_price, p.product_pic AS image_path,
                    p.is_active,
                    stock.product_quantity AS stock
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_PRODUCT_STOCK_TABLE}` stock ON c.product_id = stock.product_id
            JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON c.product_id = p.id
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)''',
        (user_account,)
    )
    return cursor.fetchall()


@db_transaction
def find_cart_item(cursor, user_account, product_id):
    # 查詢該會員購物車中是否已存在指定商品，回傳購物車 id 與數量，不存在回傳 None
    cursor.execute(
        f'''SELECT c.id, c.quantity FROM `{BRANCH_C_CART_TABLE}` c
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)
            AND c.product_id = %s''',
        (user_account, product_id)
    )
    return cursor.fetchone()


@db_transaction
def update_cart_qty(cursor, item_id, quantity):
    # 更新購物車中指定項目的數量
    cursor.execute(
        f'UPDATE `{BRANCH_C_CART_TABLE}` SET quantity = %s WHERE id = %s',
        (quantity, item_id)
    )


@db_transaction
def upsert_cart(cursor, user_account, product_id):
    # 加入購物車，若該商品已存在則數量 +1，不存在則新增一筆數量為 1 的記錄
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_CART_TABLE}` (user_id, product_id, quantity)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s), %s, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1''',
        (user_account, product_id)
    )


@db_transaction
def remove_cart_item(cursor, item_id, user_account):
    # 從購物車移除指定商品，驗證必須屬於本人才能刪除
    cursor.execute(
        f'''DELETE FROM `{BRANCH_C_CART_TABLE}`
            WHERE id = %s
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)''',
        (item_id, user_account)
    )


@db_transaction
def clear_cart(cursor, user_account):
    # 清空該會員的整個購物車，結帳完成後呼叫
    cursor.execute(
        f'''DELETE FROM `{BRANCH_C_CART_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)''',
        (user_account,)
    )


@db_transaction
def get_cart_item_stock(cursor, item_id, user_account):
    cursor.execute(
        f'''SELECT stock.product_quantity
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_PRODUCT_STOCK_TABLE}` stock ON c.product_id = stock.product_id
            WHERE c.id = %s AND c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)''',
        (item_id, user_account)
    )
    row = cursor.fetchone()
    return row['product_quantity'] if row else None
