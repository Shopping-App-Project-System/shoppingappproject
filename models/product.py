"""商品查詢、上架與庫存。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import (
    BRANCH_B_PRODUCTS_TABLE,
    BRANCH_B_PRODUCT_STOCK_TABLE,
)


@db_transaction
def index(cursor):
    # 取得所有上架且有庫存的商品，供首頁列表使用
    cursor.execute("""
        SELECT
            p.id,
            p.id,
            p.product_pic,
            p.original_price,
            p.sale_price,
            p.name,
            p.description,
            p.category
        FROM products p
        INNER JOIN product_stock ps ON p.id = ps.product_id
        WHERE p.is_active = 1 AND ps.product_quantity > 0
    """)
    return cursor.fetchall()


@db_transaction
def search_categories(cursor, category, keyword):
    sql = """
     SELECT p.id, p.product_pic, p.original_price, p.sale_price, 
            p.name, p.description, p.category, p.tag,
            ps.product_quantity
     FROM products p
     LEFT JOIN product_stock ps ON p.id = ps.product_id
     WHERE p.is_active = 1
 """
    params = []

    if category:
        sql += " AND p.category = %s"
        params.append(category)
        
    if keyword:
        sql += " AND (p.id LIKE %s OR p.name LIKE %s OR p.description LIKE %s)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")

    cursor.execute(sql, params)
    return cursor.fetchall()


@db_transaction
def get_product_by_id(cursor, product_id):
    # 依 id 取得單一商品的完整資料
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    return cursor.fetchone()


@db_transaction
def get_product_stock(cursor, product_id):
    # 依商品 id 取得庫存紀錄
    cursor.execute("SELECT * FROM product_stock WHERE product_id = %s", (product_id,))
    return cursor.fetchone()


@db_transaction
def get_product_pics(cursor, product_id):
    # 取得商品的所有附圖
    cursor.execute("SELECT product_pic FROM product_pics WHERE product_id = %s", (product_id,))
    return cursor.fetchall()


@db_transaction
def get_product(cursor, product_id):
    # 依商品 id 取得商品基本資料（id、名稱）
    cursor.execute(
        f'SELECT id, name FROM `{BRANCH_B_PRODUCTS_TABLE}` WHERE id = %s',
        (product_id,)
    )
    return cursor.fetchone()


@db_transaction
def deduct_product_stock(cursor, product_id, quantity):
    # 扣減商品庫存，結帳建立訂單後呼叫
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity - %s WHERE product_id = %s",
        (quantity, product_id)
    )


@db_transaction
def restore_product_stock(cursor, product_id, quantity):
    # 補回商品庫存，取消訂單後呼叫
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity + %s WHERE product_id = %s",
        (quantity, product_id)
    )


@db_transaction
def hard_delete_product(cursor, product_id):
    cursor.execute(f"DELETE FROM `{BRANCH_B_PRODUCT_STOCK_TABLE}` WHERE product_id = %s", (product_id,))
    cursor.execute(f"DELETE FROM `{BRANCH_B_PRODUCTS_TABLE}` WHERE id = %s", (product_id,))


@db_transaction
def add_product(cursor, name, original_price, sale_price, description, img_filename, mc_item_id, category=None):
    # 新增商品，預設為上架狀態，回傳新商品的 id
    cursor.execute(f"""
        INSERT INTO `{BRANCH_B_PRODUCTS_TABLE}`
        (`mc_item_id`, `name`, `original_price`, `sale_price`, `description`, `product_pic`, `category`, `is_active`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
    """, (mc_item_id, name, original_price, sale_price, description, img_filename, category))
    return cursor.lastrowid


@db_transaction
def add_product_stock(cursor, product_id, quantity):
    # 為商品建立庫存紀錄（商品入庫）
    cursor.execute("""
        INSERT INTO `product_stock` (product_id, product_quantity)
        VALUES (%s, %s)
    """, (product_id, quantity))


@db_transaction
def set_product_stock(cursor, product_id, quantity):
    # 直接把商品庫存設為指定數量(修改商品時使用)。
    # 若該商品還沒有庫存紀錄,自動建立一筆;否則更新。
    cursor.execute("""
        SELECT 1 FROM `product_stock` WHERE product_id = %s
    """, (product_id,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE `product_stock` SET product_quantity = %s WHERE product_id = %s
        """, (quantity, product_id))
    else:
        cursor.execute("""
            INSERT INTO `product_stock` (product_id, product_quantity) VALUES (%s, %s)
        """, (product_id, quantity))


@db_transaction
def set_product_active(cursor, product_id, is_active):
    # 設定商品上下架狀態，is_active=1 為上架，0 為下架
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET `is_active` = %s
        WHERE `id` = %s
    """, (is_active, product_id))


@db_transaction
def update_product(cursor, set_: dict, product_id):
    """
    更新商品資料。
    set_       : 要更新的欄位 dict，例如 {"name": "新名稱", "original_price": 100, ...}
    product_id : 要更新的商品 ID
    """
    if not set_:
        return
    set_key, set_value = tuple(set_.keys()), tuple(set_.values())
    set_sql = ", ".join(f"`{key}` = %s" for key in set_key)
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET {set_sql}
        WHERE `id` = %s
    """, set_value + (product_id,))


@db_transaction
def get_all_products(cursor):
    # 取得所有未刪除的商品清單（含庫存、分類），供後台管理頁使用
    cursor.execute(f"""
        SELECT p.id, p.name, p.product_pic, p.original_price,
               p.sale_price, p.is_active, p.category, ps.product_quantity
        FROM `{BRANCH_B_PRODUCTS_TABLE}` p
        LEFT JOIN product_stock ps ON p.id = ps.product_id
        WHERE p.is_deleted = 0
    """)
    return cursor.fetchall()


@db_transaction
def soft_delete_product(cursor, product_id):
    # 軟刪除商品，將 is_deleted 設為 1，資料不實際移除
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET is_deleted = 1
        WHERE id = %s
    """, (product_id,))


@db_transaction
def restore_product(cursor, product_id):
    # 還原已軟刪除的商品
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET is_deleted = 0
        WHERE id = %s
    """, (product_id,))
