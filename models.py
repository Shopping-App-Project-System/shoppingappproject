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
        SELECT id, product_code, product_pic, original_price, sale_price, name, description, category, tag
        FROM products
        WHERE is_active = 1
    """
    params = []

    if cat_id:
        sql += " AND category = %s"
        params.append(cat_id)
    if keyword:
        sql += " AND (product_code LIKE %s OR name LIKE %s OR description LIKE %s)"
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
            p.product_code,
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

# @db_transaction
# def get_product_detail(self, cursor, product_id):
#     cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
#     product = cursor.fetchone()

#     if not product:
#         return None, None, []

#     cursor.execute("SELECT * FROM product_stock WHERE product_id = %s", (product['id'],))
#     stock = cursor.fetchone()

#     cursor.execute("SELECT product_pic FROM product_pics WHERE product_id = %s", (product['id'],))
#     extra_pics = cursor.fetchall()

#     return product, stock, extra_pics
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
                   p.name, p.sale_price AS price, p.product_pic AS image_path
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_TABLE}` p ON c.product_id = p.id
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (user_account,)
    )
    return cursor.fetchall()



# @db_transaction
# def add_cart_item(self, cursor, user_account, product_id):
#     cursor.execute(
#         f'SELECT id, name FROM `{settings.BRANCH_B_TABLE}` WHERE id = ?',
#         (product_id,)
#     )
#     product = cursor.fetchone()
#     if product:
#         product_name = product['name']

#         cursor.execute(
#             f'''SELECT c.id, c.quantity FROM `{settings.BRANCH_C_CART_TABLE}` c
#                 WHERE c.user_id = (SELECT id FROM `{settings.BRANCH_A_TABLE}` WHERE user_account = ?)
#                 AND c.product_id = ?''',
#             (user_account, product_id)
#         )
#         existing = cursor.fetchone()
#         if existing:
#             cursor.execute(
#                 f'UPDATE `{settings.BRANCH_C_CART_TABLE}` SET quantity = ? WHERE id = ?',
#                 (existing['quantity'] + 1, existing['id'])
#             )
#         else:
#             cursor.execute(
#                 f'''INSERT INTO `{settings.BRANCH_C_CART_TABLE}` (user_id, product_id, quantity)
#                     VALUES ((SELECT id FROM `{settings.BRANCH_A_TABLE}` WHERE user_account = ?), ?, 1)''',
#                 (user_account, product_id)
#             )
#         return product_name
# _____________________________________________________________________________________________________
# >>>
# 分解成四個
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
# _____________________________________________________________________________________________________
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

# @db_transaction
# def create_order(self, cursor, user_account, total, payment_method,
#                  delivery_method, address, note, items):
#     cursor.execute(
#         f'''INSERT INTO `{settings.BRANCH_C_ORDER_TABLE}`
#             (user_id, total, payment_method, delivery_method, address, note, status)
#             VALUES ((SELECT id FROM `{settings.BRANCH_A_TABLE}` WHERE user_account = ?),?,?,?,?,?,'處理中')''',
#         (user_account, total, payment_method, delivery_method, address, note)
#     )
#     order_id = cursor.lastrowid
#     for item in items:
#         cursor.execute(
#             f'INSERT INTO `{settings.BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
#             (order_id, item['product_id'], item['quantity'], item['price'])
#         )
#     return order_id
# ___________________________________________________________________________________________________________________________________
# >>>
# 拆成兩個
@db_transaction
def insert_order(cursor, user_account, total, payment_method, delivery_method, address, note):
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_ORDER_TABLE}`
            (user_id, total, payment_method, delivery_method, address, note, status)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?),?,?,?,?,?,'處理中')''',
        (user_account, total, payment_method, delivery_method, address, note)
    )
    return cursor.lastrowid

@db_transaction
def insert_order_item(cursor, order_id, product_id, quantity, price):
    cursor.execute(
        f'INSERT INTO `{BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
        (order_id, product_id, quantity, price)
    )
# ___________________________________________________________________________________________________________________________________

@db_transaction
def get_orders(cursor, user_account):
    cursor.execute(
        f'''SELECT id, total, payment_method, delivery_method,
                   address, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            ORDER BY created_at DESC''',
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
            AND (address LIKE ? OR status LIKE ?)
            ORDER BY created_at DESC''',
        (user_account, like_keyword, like_keyword)
    )
    return cursor.fetchall()

# @db_transaction
# def cancel_order(cursor, order_id, user_account):
#     cursor.execute(
#         f'''SELECT id FROM `{settings.BRANCH_C_ORDER_TABLE}`
#             WHERE id = ?
#             AND user_id = (SELECT id FROM `{settings.BRANCH_A_TABLE}` WHERE user_account = ?)
#             AND status = '處理中' ''',
#         (order_id, user_account)
#     )
    
#     if cursor.fetchone() is None:
#         return False
#     cursor.execute(
#         f"UPDATE `{settings.BRANCH_C_ORDER_TABLE}` SET status = '已取消' WHERE id = ?",
#         (order_id,)
#     )
#     return True
# ___________________________________________________________________________________________________________________________________
# >>>
# 拆成兩個
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
@db_transaction
def add_product(cursor, name, price, description, img_filename):
    cursor.execute(f"""
        INSERT INTO `{BRANCH_B_TABLE}`
        (`name`, `original_price`, `description`, `product_pic`, `is_active`)
        VALUES (?, ?, ?, ?, 1)
    """, (name, price, description, img_filename))
    
@db_transaction
def set_product_active(cursor, product_id, is_active):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET `is_active` = ?
        WHERE `id` = ?
    """, (is_active, product_id))
    
# 查所有商品（含下架，排除已刪除）
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

# 軟刪除商品
@db_transaction
def soft_delete_product(cursor, product_id):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_TABLE}`
        SET is_deleted = 1
        WHERE id = ?
    """, (product_id,))

# 寫入操作紀錄
@db_transaction
def add_log(cursor, admin_account, action, product_id, product_name):
    cursor.execute("""
        INSERT INTO manage_log
        (admin_account, action, product_id, product_name)
        VALUES (?, ?, ?, ?)
    """, (admin_account, action, product_id, product_name))

# 查操作紀錄
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
if __name__ == "__main__":
    ...