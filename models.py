from settings import BRANCH_A_TABLE,BRANCH_C_CART_TABLE,BRANCH_B_TABLE,BRANCH_C_ORDER_TABLE,BRANCH_C_ORDER_ITEMS_TABLE
from db import db_transaction


# ── Branch A：使用者帳號相關方法 ────────────────────────────────────────────────────

@db_transaction
def createUser(cursor, user_name, user_account, user_password, user_mobile, user_email, user_address):
    cursor.execute(f"""
        INSERT INTO `{BRANCH_A_TABLE}`
        (`user_name`,`user_account`,`user_password`,`user_mobile`,`user_email`,`user_address`)
        VALUES (?,?,?,?,?,?)
    """, (user_name, user_account, user_password, user_mobile, user_email, user_address))

@db_transaction
def updateUser(cursor, set_: dict, where: dict):
    set_key, set_value = tuple(set_.keys()), tuple(set_.values())
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
    where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)

    cursor.execute(f"""
        UPDATE `{BRANCH_A_TABLE}`
        SET {set_sql}
        WHERE {where_sql}
    """, set_value + where_value)

@db_transaction
def getUser(cursor, where: dict, *selections):
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    if selections == ():
        selections = "*"
    else:
        selections = ",".join(f"`{selection}`" for selection in selections)

    where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)

    cursor.execute(f"""
        SELECT {selections}
        FROM `{BRANCH_A_TABLE}`
        WHERE {where_sql}
    """, where_value)

    users = cursor.fetchall()
    if users != []:
        users = users[0]
        if len(users) == 1:
            return list(users.values())[0]
        return users
    return None


# ── Branch B：商品卡陳列 ──────────────────────────────────────────────────────────

@db_transaction
def search_categories(cursor, cat_id, keyword):
    sql = """
        SELECT id, product_pic, original_price, sale_price, name, description, category, tag
        FROM products
        WHERE is_active = 1
    """
    params = []

    if cat_id:
        sql += " AND category = %s"
        params.append(cat_id)
    if keyword:
        sql += " AND (id LIKE %s OR name LIKE %s OR description LIKE %s)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")

    cursor.execute(sql, params)
    return cursor.fetchall()

@db_transaction
def get_all_categories(cursor):
    cursor.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE is_active = 1 AND category IS NOT NULL
    """)
    return cursor.fetchall()

@db_transaction
def index(cursor):
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
def get_product_by_id(cursor, product_id):
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    return cursor.fetchone()

@db_transaction
def get_product_stock(cursor, product_id):
    cursor.execute("SELECT * FROM product_stock WHERE product_id = %s", (product_id,))
    return cursor.fetchone()

@db_transaction
def get_product_pics(cursor, product_id):
    cursor.execute("SELECT product_pic FROM product_pics WHERE product_id = %s", (product_id,))
    return cursor.fetchall()


# ── Branch C：購物車 ──────────────────────────────────────────────────────────

@db_transaction
def get_cart_items(cursor, user_account):
    cursor.execute(
        f'''SELECT c.id, c.user_id, c.product_id, c.quantity,
                    p.name, COALESCE(p.sale_price, p.original_price) AS price, p.product_pic AS image_path
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_TABLE}` p ON c.product_id = p.id
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (user_account,)
    )
    return cursor.fetchall()


@db_transaction
def get_product(cursor, product_id):
    cursor.execute(
        f'SELECT id, name FROM `{BRANCH_B_TABLE}` WHERE id = ?',
        (product_id,)
    )
    return cursor.fetchone()

@db_transaction
def find_cart_item(cursor, user_account, product_id):
    cursor.execute(
        f'''SELECT c.id, c.quantity FROM `{BRANCH_C_CART_TABLE}` c
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND c.product_id = ?''',
        (user_account, product_id)
    )
    return cursor.fetchone()

@db_transaction
def update_cart_qty(cursor, item_id, quantity):
    cursor.execute(
        f'UPDATE `{BRANCH_C_CART_TABLE}` SET quantity = ? WHERE id = ?',
        (quantity, item_id)
    )

@db_transaction
def upsert_cart(cursor, user_account, product_id):
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_CART_TABLE}` (user_id, product_id, quantity)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?), ?, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1''',
        (user_account, product_id)
    )

@db_transaction
def remove_cart_item(cursor, item_id, user_account):
    cursor.execute(
        f'''DELETE FROM `{BRANCH_C_CART_TABLE}`
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (item_id, user_account)
    )

@db_transaction
def clear_cart(cursor, user_account):
    cursor.execute(
        f'''DELETE FROM `{BRANCH_C_CART_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (user_account,)
    )


# ── Branch C：訂單 ────────────────────────────────────────────────────────────

@db_transaction
def insert_order(cursor, user_account, total, payment_method, delivery_method, address, note, credit_card_number=None):
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_ORDER_TABLE}`
            (user_id, total, payment_method, delivery_method, address, note, status, credit_card_number)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?),?,?,?,?,?,'處理中',?)''',
        (user_account, total, payment_method, delivery_method, address, note, credit_card_number)
    )
    return cursor.lastrowid

@db_transaction
def insert_order_item(cursor, order_id, product_id, quantity, price):
    cursor.execute(
        f'INSERT INTO `{BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
        (order_id, product_id, quantity, price)
    )

@db_transaction
def get_all_orders(cursor, user_account):
    cursor.execute(
        f'''SELECT id, total, payment_method, delivery_method,
                   address, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            ORDER BY created_at ASC''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def get_orders(cursor, user_account):
    cursor.execute(
        f'''SELECT id, total, payment_method, delivery_method,
                   address, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status != '已取消'
            ORDER BY created_at ASC''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def search_orders(cursor, user_account, keyword):
    like_keyword = "%" + keyword + "%"
    cursor.execute(
        f'''SELECT id, total, payment_method, delivery_method,
                   address, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status != '已取消'
            AND (address LIKE ? OR status LIKE ?)
            ORDER BY created_at DESC''',
        (user_account, like_keyword, like_keyword)
    )
    return cursor.fetchall()

@db_transaction
def get_order(cursor, order_id, user_account):
    cursor.execute(
        f'''SELECT id FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status = '處理中' ''',
        (order_id, user_account)
    )
    return cursor.fetchone()

@db_transaction
def cancel_order(cursor, order_id):
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_TABLE}` SET status = '已取消' WHERE id = ?",
        (order_id,)
    )


# _______________________________________________________________
# 商品管理
@db_transaction
def add_product(cursor, name, original_price, sale_price, description, img_filename):
    cursor.execute(f"""
        INSERT INTO `{BRANCH_B_TABLE}`
        (`name`, `original_price`, `sale_price`, `description`, `product_pic`, `is_active`)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (name, original_price, sale_price, description, img_filename))

@db_transaction
def set_product_active(cursor, product_id, is_active):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET `is_active` = ?
        WHERE `id` = ?
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
    set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET {set_sql}
        WHERE `id` = ?
    """, set_value + (product_id,))

@db_transaction
def get_all_products(cursor):
    cursor.execute(f"""
        SELECT p.id, p.name, p.product_pic, p.original_price,
               p.sale_price, p.is_active, ps.product_quantity
        FROM `{BRANCH_B_TABLE}` p
        LEFT JOIN product_stock ps ON p.id = ps.product_id
        WHERE p.is_deleted = 0
    """)
    return cursor.fetchall()

@db_transaction
def soft_delete_product(cursor, product_id):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET is_deleted = 1
        WHERE id = ?
    """, (product_id,))

@db_transaction
def add_log(cursor, admin_account, action, product_id, product_name):
    cursor.execute("""
        INSERT INTO manage_log
        (admin_account, action, product_id, product_name)
        VALUES (?, ?, ?, ?)
    """, (admin_account, action, product_id, product_name))

@db_transaction
def get_logs(cursor):
    cursor.execute("""
        SELECT * FROM manage_log
        ORDER BY created_at DESC
    """)
    return cursor.fetchall()

@db_transaction
def restore_product(cursor, product_id):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET is_deleted = 0
        WHERE id = ?
    """, (product_id,))


# ── 信用卡管理 ────────────────────────────────────────────────────────────────
# ⚠️ 注意：以下函式直接存取完整卡號，僅適用於學校作業/示意用途。
#    正式環境請改為儲存金流商產生的 token。

@db_transaction
def get_member_cards(cursor, user_account):
    """
    取得指定會員的所有信用卡，預設卡排在最前面。
    """
    cursor.execute(
        f"""SELECT mc.id, mc.card_number, mc.expiry, mc.holder_name, mc.is_default, mc.created_at
            FROM `member_cards` mc
            WHERE mc.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            ORDER BY mc.is_default DESC, mc.created_at DESC""",
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def add_member_card(cursor, user_account, card_number, expiry, holder_name, is_default):
    """
    為會員新增一張信用卡。
    若 is_default=1，會先把該會員其他卡的 is_default 全部設為 0，避免有兩張預設卡。
    """
    if is_default:
        cursor.execute(
            f"""UPDATE `member_cards`
                SET is_default = 0
                WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
            (user_account,)
        )

    cursor.execute(
        f"""INSERT INTO `member_cards`
            (user_id, card_number, expiry, holder_name, is_default)
            VALUES (
                (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?),
                ?, ?, ?, ?
            )""",
        (user_account, card_number, expiry, holder_name, is_default)
    )

@db_transaction
def delete_member_card(cursor, user_account, card_id):
    """
    刪除會員的信用卡（限本人）。
    WHERE 條件多帶一個 user_id 比對，避免有人改 hidden input 刪別人的卡。
    """
    cursor.execute(
        f"""DELETE FROM `member_cards`
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (card_id, user_account)
    )

@db_transaction
def set_default_card(cursor, user_account, card_id):
    """
    把指定卡片設為預設卡，同時把該會員其他卡設為非預設。
    """
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 0
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (user_account,)
    )
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 1
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (card_id, user_account)
    )


if __name__ == "__main__":
    ...
