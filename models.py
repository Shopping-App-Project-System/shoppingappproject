from settings import (BRANCH_A_TABLE,
                      
                      BRANCH_B_PRODUCTS_TABLE,
                      BRANCH_B_PRODUCT_CATEGORY_TABLE,
                      BRANCH_B_PRODUCT_PICS_TABLE,
                      BRANCH_B_PRODUCT_STOCK_TABLE,
                      
                      BRANCH_C_CART_TABLE,
                      BRANCH_C_ORDER_TABLE,
                      BRANCH_C_ORDER_ITEMS_TABLE)

from db import db_transaction


# ── Branch A:使用者帳號相關方法 ────────────────────────────────────────────────────

@db_transaction
def createUser(cursor, user_name, user_account, user_password, user_mobile, user_email, user_address):
    # 新增會員帳號
    cursor.execute(f"""
        INSERT INTO {BRANCH_A_TABLE}
        (`user_name`,`user_account`,`user_password`,`user_mobile`,`user_email`,`user_address`)
        VALUES (?,?,?,?,?,?)
    """, (user_name, user_account, user_password, user_mobile, user_email, user_address))

@db_transaction
def updateUser(cursor, set_: dict, where: dict):
    # 更新會員資料，set_ 為要更新的欄位，where 為篩選條件
    set_key, set_value = tuple(set_.keys()), tuple(set_.values())
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
    where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)

    cursor.execute(f"""
        UPDATE {BRANCH_A_TABLE}
        SET {set_sql}
        WHERE {where_sql}
    """, set_value + where_value)

@db_transaction
def getUser(cursor, where: dict, *selections):
    # 依條件查詢會員資料，selections 為要取得的欄位，不傳則取全部
    # 只有一個欄位時直接回傳值，多個欄位回傳 dict，找不到回傳 None
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    if selections == ():
        selections = "*"
    else:
        selections = ",".join(f"`{selection}`" for selection in selections)

    where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)

    cursor.execute(f"""
        SELECT {selections}
        FROM {BRANCH_A_TABLE}
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
def search_categories(cursor, category, keyword):
    sql = """
     SELECT p.id, p.product_pic, p.original_price, p.sale_price, 
            p.name, p.description, pc.category, p.tag,
            ps.product_quantity
     FROM products p
     LEFT JOIN product_stock ps ON p.id = ps.product_id
     LEFT JOIN product_category pc ON p.category = pc.id   
     WHERE p.is_active = 1
 """
    params = []

    if category:
        sql += " AND pc.category = %s"
        params.append(category)  
        
    if keyword:
        sql += " AND (p.id LIKE %s OR p.name LIKE %s OR p.description LIKE %s)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")

    cursor.execute(sql, params)
    return cursor.fetchall()

@db_transaction
def get_all_categories(cursor):
    cursor.execute("""
        SELECT DISTINCT pc.category 
        FROM product_category pc
        LEFT JOIN products p ON p.category = pc.id
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
                    p.name, COALESCE(p.sale_price, p.original_price) AS price, p.product_pic AS image_path,
                    p.is_active,
                    stock.product_quantity AS stock
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_PRODUCT_STOCK_TABLE}` stock ON c.product_id = stock.product_id
            JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON c.product_id = p.id
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def get_product(cursor, product_id):
    cursor.execute(
        f'SELECT id, name FROM `{BRANCH_B_PRODUCTS_TABLE}` WHERE id = ?',
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

@db_transaction
def get_cart_item_stock(cursor, item_id, user_account):
    cursor.execute(
        f'''SELECT stock.product_quantity
            FROM `{BRANCH_C_CART_TABLE}` c
            JOIN `{BRANCH_B_PRODUCT_STOCK_TABLE}` stock ON c.product_id = stock.product_id
            WHERE c.id = ? AND c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (item_id, user_account)
    )
    row = cursor.fetchone()
    return row['product_quantity'] if row else None


# ── Branch C：訂單 ────────────────────────────────────────────────────────────

@db_transaction
def insert_order(cursor, user_account, total, payment_method, note, credit_card_number=None):
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_ORDER_TABLE}`
            (user_id, total, payment_method, note, status, credit_card_number)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?),?,?,?,'已完成',?)''',
        (user_account, total, payment_method, note, credit_card_number)
    )
    return cursor.lastrowid

@db_transaction
def insert_order_item(cursor, order_id, product_id, quantity, price):
    cursor.execute(
        f'INSERT INTO `{BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
        (order_id, product_id, quantity, price)
    )
    return cursor.lastrowid

@db_transaction
def get_order_items(cursor, order_id):
    cursor.execute(
        f'SELECT product_id, quantity FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` WHERE order_id = ?',
        (order_id,)
    )
    return cursor.fetchall()

@db_transaction
def get_order_items_detail(cursor, order_id):
    cursor.execute(
        f'''SELECT oi.quantity, oi.price,
                   p.name, p.product_pic
            FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` oi
            JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON oi.product_id = p.id
            WHERE oi.order_id = ?''',
        (order_id,)
    )
    return cursor.fetchall()

@db_transaction
def get_all_orders(cursor, user_account):
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            ORDER BY created_at ASC''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def get_orders(cursor, user_account):
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            ORDER BY created_at ASC''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def search_orders(cursor, user_account, keyword):
    like_keyword = "%" + keyword + "%"
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status LIKE ?
            ORDER BY created_at DESC''',
        (user_account, like_keyword)
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

@db_transaction
def deduct_product_stock(cursor, product_id, quantity):
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity - ? WHERE product_id = ?",
        (quantity, product_id)
    )

@db_transaction
def restore_product_stock(cursor, product_id, quantity):
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity + ? WHERE product_id = ?",
        (quantity, product_id)
    )

@db_transaction
def get_order_item_by_serial(cursor, serial_code):
    cursor.execute(
        f"""SELECT * 
            FROM {BRANCH_C_ORDER_ITEMS_TABLE}
            WHERE `serial_code` = ? AND `is_redeemed` = ?""",
        (serial_code, 0)
    )
    return cursor.fetchone()

@db_transaction
def redeem_serial(cursor, serial_code):
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_ITEMS_TABLE}` SET is_redeemed = 1 WHERE serial_code = ?",
        (serial_code,)
    )

@db_transaction
def update_order_item_serial(cursor, order_item_id, serial_code):
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_ITEMS_TABLE}` SET serial_code = ? WHERE id = ?",
        (serial_code, order_item_id)
    )


# ==============================================================
# 【備用區塊 — 雙帳號設計，目前已停用，請勿刪除】
#
# 此區塊是「白癡版本」留下的舊設計：
#   user_account（網站帳號）與 minecraft_name（MC角色名）分開存放。
#   若未來要支援「玩家可以綁定不同名稱的 MC 帳號」，
#   可以還原此區塊，並在 user 資料表加回 minecraft_name 欄位，
#   同時把 mc_bridge.py 的 give_item / notify_player 改回呼叫這裡的版本。
#
# 還原步驟：
#   1. user 資料表加欄位：ALTER TABLE user ADD COLUMN minecraft_name VARCHAR(50) NULL;
#   2. 把下方註解全部取消
#   3. 把 mc_bridge.py 的 give_item / notify_player 改成呼叫此處的版本
#   4. Shopping_services.py 的 import 改回從 models import
# ==============================================================

# import logging
# from mcrcon import MCRcon, MCRconException
# from settings import MC_RCON_HOST, MC_RCON_PORT, MC_RCON_PASSWORD
#
# _rcon_logger = logging.getLogger(__name__)
# RCON_HOST = MC_RCON_HOST
# RCON_PORT = MC_RCON_PORT
# RCON_PASSWORD = MC_RCON_PASSWORD
#
#
# def _rcon_send(command):
#     with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
#         return mcr.command(command)
#
#
# def rcon_is_player_online(player_name):
#     try:
#         response = _rcon_send("list")
#     except (MCRconException, ConnectionError, OSError) as e:
#         _rcon_logger.warning("RCON list 失敗: %s", e)
#         return False
#     if ":" not in response:
#         return False
#     online_part = response.split(":", 1)[1]
#     names = [n.strip() for n in online_part.split(",") if n.strip()]
#     return player_name in names
#
#
# def rcon_give_item(player_name, item_id, quantity, nbt=None):
#     if nbt:
#         cmd = f"give {player_name} {item_id}{nbt} {quantity}"
#     else:
#         cmd = f"give {player_name} {item_id} {quantity}"
#     try:
#         response = _rcon_send(cmd)
#     except (MCRconException, ConnectionError, OSError) as e:
#         _rcon_logger.exception("RCON give 失敗")
#         return False, f"RCON error: {e}"
#     failed_markers = ("No player", "Unknown", "Incorrect", "Expected", "is not a valid")
#     if any(m in response for m in failed_markers):
#         return False, response
#     return True, response
#
#
# @db_transaction
# def get_user_minecraft_name(cursor, user_account):
#     """取得會員綁定的 Minecraft 角色名（需要 user 表有 minecraft_name 欄位）"""
#     cursor.execute(
#         f"SELECT minecraft_name FROM `{BRANCH_A_TABLE}` WHERE user_account = ?",
#         (user_account,)
#     )
#     row = cursor.fetchone()
#     if not row:
#         return None
#     return row['minecraft_name'] if isinstance(row, dict) else row[0]
#
#
# def give_item(user_account, mc_item_id, quantity, nbt=None):
#     """
#     查資料庫取得 minecraft_name，確認在線後發道具。
#     回傳 (ok: bool, response: str)
#     """
#     player_name = get_user_minecraft_name(user_account)
#     if not player_name:
#         return False, "玩家未綁定 minecraft_name"
#     if not rcon_is_player_online(player_name):
#         return False, f"玩家 {player_name} 不在線上"
#     return rcon_give_item(player_name, mc_item_id, quantity, nbt)
#
#
# def notify_player(user_account, message):
#     """
#     查資料庫取得 minecraft_name，發送遊戲內訊息。
#     回傳 (ok: bool, response: str)
#     """
#     player_name = get_user_minecraft_name(user_account)
#     if not player_name:
#         return False, "玩家未綁定 minecraft_name"
#     try:
#         response = _rcon_send(f"tell {player_name} {message}")
#     except (MCRconException, ConnectionError, OSError) as e:
#         _rcon_logger.warning("RCON tell 失敗: %s", e)
#         return False, f"RCON error: {e}"
#     failed_markers = ("No player", "Unknown", "Incorrect", "Expected")
#     if any(m in response for m in failed_markers):
#         return False, response
#     return True, response
#
#
# def deliver_cart_to_player(user_account, cart_items):
#     """
#     結帳時整批發貨給玩家，玩家必須在線才能購買。
#     cart_items 格式: [{'mc_item_id': 'minecraft:diamond', 'quantity': 64}, ...]
#     回傳: (ok: bool, message: str, details: list)
#     """
#     player_name = get_user_minecraft_name(user_account)
#     if not player_name:
#         return False, "尚未綁定 Minecraft 角色名", []
#     if not rcon_is_player_online(player_name):
#         return False, f"玩家 {player_name} 不在線上，請先進入遊戲再購買", []
#     details = []
#     all_ok = True
#     for item in cart_items:
#         mc_item_id = item.get('mc_item_id')
#         if not mc_item_id:
#             details.append({'item': item, 'ok': False, 'msg': '商品未設定 mc_item_id'})
#             all_ok = False
#             continue
#         ok, response = rcon_give_item(
#             player_name=player_name,
#             item_id=mc_item_id,
#             quantity=item['quantity'],
#         )
#         details.append({'item': item, 'ok': ok, 'msg': response})
#         if not ok:
#             all_ok = False
#     return all_ok, "OK" if all_ok else "部分發送失敗", details


# ── Branch D：商品管理（後台） ────────────────────────────────────────────────

@db_transaction
def add_product(cursor, name, original_price, sale_price, description, img_filename, mc_item_id):
    cursor.execute(f"""
        INSERT INTO `{BRANCH_B_PRODUCTS_TABLE}`
        (`mc_item_id`, `name`, `original_price`, `sale_price`, `description`, `product_pic`, `is_active`)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (mc_item_id, name, original_price, sale_price, description, img_filename))
    return cursor.lastrowid

@db_transaction
def add_product_stock(cursor, product_id, quantity):
    cursor.execute("""
        INSERT INTO `product_stock` (product_id, product_quantity)
        VALUES (?, ?)
    """, (product_id, quantity))

@db_transaction
def set_product_stock(cursor, product_id, quantity):
    cursor.execute("""
        SELECT 1 FROM `product_stock` WHERE product_id = ?
    """, (product_id,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE `product_stock` SET product_quantity = ? WHERE product_id = ?
        """, (quantity, product_id))
    else:
        cursor.execute("""
            INSERT INTO `product_stock` (product_id, product_quantity) VALUES (?, ?)
        """, (product_id, quantity))

@db_transaction
def set_product_active(cursor, product_id, is_active):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET `is_active` = ?
        WHERE `id` = ?
    """, (is_active, product_id))

@db_transaction
def update_product(cursor, set_: dict, product_id):
    if not set_:
        return
    set_key, set_value = tuple(set_.keys()), tuple(set_.values())
    set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET {set_sql}
        WHERE `id` = ?
    """, set_value + (product_id,))

@db_transaction
def get_all_products(cursor):
    cursor.execute(f"""
        SELECT p.id, p.name, p.product_pic, p.original_price,
               p.sale_price, p.is_active, ps.product_quantity
        FROM `{BRANCH_B_PRODUCTS_TABLE}` p
        LEFT JOIN product_stock ps ON p.id = ps.product_id
        WHERE p.is_deleted = 0
    """)
    return cursor.fetchall()

@db_transaction
def soft_delete_product(cursor, product_id):
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
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
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET is_deleted = 0
        WHERE id = ?
    """, (product_id,))


# ── 信用卡管理 ────────────────────────────────────────────────────────────────
# ⚠️ 注意：以下函式直接存取完整卡號，僅適用於學校作業/示意用途。

@db_transaction
def get_member_cards(cursor, user_account):
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
    cursor.execute(
        f"""DELETE FROM `member_cards`
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (card_id, user_account)
    )

@db_transaction
def clear_default_cards(cursor, user_account):
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 0
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (user_account,)
    )

@db_transaction
def set_default_card(cursor, user_account, card_id):
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 1
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (card_id, user_account)
    )

# ── manage_log 報表 ─────────────────────────────────

@db_transaction
def get_log_months(cursor):
    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') AS month,
               COUNT(*) AS log_count
        FROM manage_log
        GROUP BY month
        ORDER BY month DESC
    """)
    return cursor.fetchall()

@db_transaction
def get_logs_by_month(cursor, month):
    cursor.execute("""
        SELECT created_at, admin_account, action, product_id, product_name
        FROM manage_log
        WHERE DATE_FORMAT(created_at, '%Y-%m') = ?
        ORDER BY created_at DESC
    """, (month,))
    return cursor.fetchall()


# ── 已完成訂單查詢 ─────────────────────────────────────────────

@db_transaction
def get_user_accounts_with_orders(cursor):
    cursor.execute(f"""
        SELECT DISTINCT u.user_account
        FROM `{BRANCH_A_TABLE}` u
        JOIN `{BRANCH_C_ORDER_TABLE}` o ON o.user_id = u.id
        WHERE o.status = '已完成'
        ORDER BY u.user_account
    """)
    return [row['user_account'] for row in cursor.fetchall()]

@db_transaction
def search_completed_orders(cursor, user_account=None, target_user=None,
                            month=None, min_total=None, max_total=None):
    sql = f"""
        SELECT o.id, o.total, o.payment_method,
               o.note, o.status, o.created_at,
               u.user_account
        FROM `{BRANCH_C_ORDER_TABLE}` o
        JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
        WHERE o.status = '已完成'
    """
    params = []

    if user_account is not None:
        sql += " AND u.user_account = ?"
        params.append(user_account)
    elif target_user:
        sql += " AND u.user_account = ?"
        params.append(target_user)

    if month:
        sql += " AND DATE_FORMAT(o.created_at, '%Y-%m') = ?"
        params.append(month)

    if min_total is not None:
        sql += " AND o.total >= ?"
        params.append(min_total)

    if max_total is not None:
        sql += " AND o.total <= ?"
        params.append(max_total)

    sql += " ORDER BY o.created_at DESC"
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()

@db_transaction
def get_order_items_with_user_check(cursor, order_id, user_account=None):
    if user_account is not None:
        cursor.execute(f"""
            SELECT 1 FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
            WHERE o.id = ? AND u.user_account = ? AND o.status = '已完成'
        """, (order_id, user_account))
        if not cursor.fetchone():
            return None
    else:
        cursor.execute(f"""
            SELECT 1 FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE id = ? AND status = '已完成'
        """, (order_id,))
        if not cursor.fetchone():
            return None

    cursor.execute(f"""
        SELECT oi.quantity, oi.price, oi.serial_code,
               p.name AS product_name, p.product_pic
        FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` oi
        JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    """, (order_id,))
    return cursor.fetchall()
