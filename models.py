from settings import (BRANCH_A_TABLE,
                      
                      BRANCH_B_PRODUCTS_TABLE,
                      BRANCH_B_PRODUCT_CATEGORY_TABLE,
                      BRANCH_B_PRODUCT_PICS_TABLE,
                      BRANCH_B_PRODUCT_STOCK_TABLE,
                      
                      BRANCH_C_CART_TABLE,
                      BRANCH_C_ORDER_TABLE,
                      BRANCH_C_ORDER_ITEMS_TABLE)

from db import db_transaction


# ── RCON:與 Minecraft 伺服器通訊 ────────────────────────────────────────────────────
# 需要 pip install mcrcon
import logging
from mcrcon import MCRcon, MCRconException

from settings import MC_RCON_HOST, MC_RCON_PORT, MC_RCON_PASSWORD

_rcon_logger = logging.getLogger(__name__)

RCON_HOST = MC_RCON_HOST
RCON_PORT = MC_RCON_PORT
RCON_PASSWORD = MC_RCON_PASSWORD


def _rcon_send(command):
    # 每次建新連線,簡單可靠
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        return mcr.command(command)


def rcon_is_player_online(player_name):
    # 用 /list 確認玩家是否在線
    try:
        response = _rcon_send("list")
    except (MCRconException, ConnectionError, OSError) as e:
        _rcon_logger.warning("RCON list 失敗: %s", e)
        return False
    if ":" not in response:
        return False
    online_part = response.split(":", 1)[1]
    names = [n.strip() for n in online_part.split(",") if n.strip()]
    return player_name in names


def rcon_give_item(player_name, item_id, quantity, nbt=None):
    # 對玩家執行 /give,回傳 (ok: bool, response: str)
    if nbt:
        cmd = f"give {player_name} {item_id}{nbt} {quantity}"
    else:
        cmd = f"give {player_name} {item_id} {quantity}"
    try:
        response = _rcon_send(cmd)
    except (MCRconException, ConnectionError, OSError) as e:
        _rcon_logger.exception("RCON give 失敗")
        return False, f"RCON error: {e}"
    failed_markers = ("No player", "Unknown", "Incorrect", "Expected", "is not a valid")
    if any(m in response for m in failed_markers):
        return False, response
    return True, response


# ── Branch A:使用者帳號相關方法 ────────────────────────────────────────────────────

@db_transaction
def createUser(cursor, user_name, user_account, user_password, user_mobile, user_email, user_address, minecraft_name):
    # 新增會員帳號,minecraft_name 為玩家綁定的 Minecraft 角色名,/give 時使用
    cursor.execute(f"""
        INSERT INTO `{BRANCH_A_TABLE}`
        (`user_name`,`user_account`,`user_password`,`user_mobile`,`user_email`,`user_address`,`minecraft_name`)
        VALUES (?,?,?,?,?,?,?)
    """, (user_name, user_account, user_password, user_mobile, user_email, user_address, minecraft_name))

@db_transaction
def is_minecraft_name_taken(cursor, minecraft_name):
    # 檢查該 Minecraft 角色名是否已被其他帳號綁定
    cursor.execute(
        f"SELECT 1 FROM `{BRANCH_A_TABLE}` WHERE minecraft_name = ?",
        (minecraft_name,)
    )
    return cursor.fetchone() is not None

@db_transaction
def updateUser(cursor, set_: dict, where: dict):
    # 更新會員資料，set_ 為要更新的欄位，where 為篩選條件
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
def search_categories(cursor, category, keyword):
    # 依分類名稱 與關鍵字搜尋上架商品，兩個條件都是選填
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
    # 取得所有上架商品的不重複分類清單
    cursor.execute("""
        SELECT DISTINCT pc.category 
        FROM product_category pc
        LEFT JOIN products p ON p.category = pc.id
    """)
    return cursor.fetchall()

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


# ── Branch C：購物車 ──────────────────────────────────────────────────────────

@db_transaction
def get_cart_items(cursor, user_account):
    # 取得該會員的所有購物車商品，JOIN 商品表取得名稱、價格、圖片，JOIN 庫存表取得剩餘庫存
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
    # 依商品 id 取得商品基本資料（id、名稱）
    cursor.execute(
        f'SELECT id, name FROM `{BRANCH_B_PRODUCTS_TABLE}` WHERE id = ?',
        (product_id,)
    )
    return cursor.fetchone()

# @db_transaction
# # def get_product_stock(cursor, product_id):
    

@db_transaction
def find_cart_item(cursor, user_account, product_id):
    # 查詢該會員購物車中是否已存在指定商品，回傳購物車 id 與數量，不存在回傳 None
    cursor.execute(
        f'''SELECT c.id, c.quantity FROM `{BRANCH_C_CART_TABLE}` c
            WHERE c.user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND c.product_id = ?''',
        (user_account, product_id)
    )
    return cursor.fetchone()

@db_transaction
def update_cart_qty(cursor, item_id, quantity):
    # 更新購物車中指定項目的數量
    cursor.execute(
        f'UPDATE `{BRANCH_C_CART_TABLE}` SET quantity = ? WHERE id = ?',
        (quantity, item_id)
    )
    


@db_transaction
def upsert_cart(cursor, user_account, product_id):
    # 加入購物車，若該商品已存在則數量 +1，不存在則新增一筆數量為 1 的記錄
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_CART_TABLE}` (user_id, product_id, quantity)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?), ?, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1''',
        (user_account, product_id)
    )

@db_transaction
def remove_cart_item(cursor, item_id, user_account):
    # 從購物車移除指定商品，驗證必須屬於本人才能刪除
    cursor.execute(
        f'''DELETE FROM `{BRANCH_C_CART_TABLE}`
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)''',
        (item_id, user_account)
    )

@db_transaction
def clear_cart(cursor, user_account):
    # 清空該會員的整個購物車，結帳完成後呼叫
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
    # 建立新訂單，狀態預設為「處理中」，回傳新訂單的 id
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_ORDER_TABLE}`
            (user_id, total, payment_method, note, status, credit_card_number)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?),?,?,?,'處理中',?)''',
        (user_account, total, payment_method, note, credit_card_number)
    )
    return cursor.lastrowid

@db_transaction
def insert_order_item(cursor, order_id, product_id, quantity, price):
    # 新增一筆訂單明細，記錄下單當下的價格
    cursor.execute(
        f'INSERT INTO `{BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
        (order_id, product_id, quantity, price)
    )
    return cursor.lastrowid

@db_transaction
def get_order_items(cursor, order_id):
    # 取得指定訂單的所有商品明細（商品 id 與數量），取消訂單補回庫存時使用
    cursor.execute(
        f'SELECT product_id, quantity FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` WHERE order_id = ?',
        (order_id,)
    )
    return cursor.fetchall()

@db_transaction
def get_order_items_detail(cursor, order_id):
    # 取得訂單明細並 JOIN 商品名稱，供會員頁訂單展開顯示使用
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
    # 取得該會員所有訂單（含已取消），依建立時間升冪排列
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
    # 取得該會員的有效訂單（排除已取消），依建立時間升冪排列
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status != '已取消'
            ORDER BY created_at ASC''',
        (user_account,)
    )
    return cursor.fetchall()

@db_transaction
def search_orders(cursor, user_account, keyword):
    # 依關鍵字搜尋該會員的有效訂單（比對地址或狀態），依建立時間降冪排列
    like_keyword = "%" + keyword + "%"
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)
            AND status != '已取消'
            AND status LIKE ?
            ORDER BY created_at DESC''',
        (user_account, like_keyword)
    )
    return cursor.fetchall()

@db_transaction
def get_order(cursor, order_id, user_account):
    # 取得指定訂單，驗證必須屬於本人且狀態為「處理中」，取消訂單前呼叫
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
    # 將指定訂單狀態更新為「已取消」
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_TABLE}` SET status = '已取消' WHERE id = ?",
        (order_id,)
    )

@db_transaction
def deduct_product_stock(cursor, product_id, quantity):
    # 扣減商品庫存，結帳建立訂單後呼叫
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity - ? WHERE product_id = ?",
        (quantity, product_id)
    )

@db_transaction
def restore_product_stock(cursor, product_id, quantity):
    # 補回商品庫存，取消訂單後呼叫
    cursor.execute(
        f"UPDATE `{BRANCH_B_PRODUCT_STOCK_TABLE}` SET product_quantity = product_quantity + ? WHERE product_id = ?",
        (quantity, product_id)
    )

# 查詢 order_items 裡 serial_code 符合且尚未兌換的那筆資料
@db_transaction
def get_order_item_by_serial(cursor, serial_code):

    cursor.execute(
                    f"""
                       SELECT * 
                       FROM {BRANCH_C_ORDER_ITEMS_TABLE}
                       WHERE `serial_code` = ? AND `is_redeemed` = ?
                   """,(serial_code,0)
                   )
    return cursor.fetchone()

# 將指定序號標記為已兌換，防止重複使用
@db_transaction
def redeem_serial(cursor, serial_code):
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_ITEMS_TABLE}` SET is_redeemed = 1 WHERE serial_code = ?",
        (serial_code,)
    )
    
# 將產生的序號寫入指定的訂單明細    
@db_transaction
def update_order_item_serial(cursor, order_item_id, serial_code):
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_ITEMS_TABLE}` SET serial_code = ? WHERE id = ?",
        (serial_code, order_item_id)
    )


# ── Minecraft 結帳即時發貨 ────────────────────────────────────────────────

@db_transaction
def get_user_minecraft_name(cursor, user_account):
    # 取得會員綁定的 Minecraft 角色名
    cursor.execute(
        f"SELECT minecraft_name FROM `{BRANCH_A_TABLE}` WHERE user_account = ?",
        (user_account,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row['minecraft_name'] if isinstance(row, dict) else row[0]


def give_item(user_account, mc_item_id, quantity, nbt=None):
    """
    供 Shopping_services 直接呼叫:依 user_account 查 minecraft_name,然後 /give。
    回傳 (ok: bool, response: str)
      - ok=False 的情況: 玩家未綁定 / 玩家不在線 / RCON 連線失敗 / /give 指令失敗
    """
    player_name = get_user_minecraft_name(user_account)
    if not player_name:
        return False, "玩家未綁定 minecraft_name"
    if not rcon_is_player_online(player_name):
        return False, f"玩家 {player_name} 不在線上"
    return rcon_give_item(player_name, mc_item_id, quantity, nbt)


def notify_player(user_account, message):
    """
    供 Shopping_services 直接呼叫:對玩家發送遊戲內訊息 (/tell)。
    回傳 (ok: bool, response: str)
    /tell 即使玩家不在線指令也會回 "No player was found",我們當失敗處理。
    """
    player_name = get_user_minecraft_name(user_account)
    if not player_name:
        return False, "玩家未綁定 minecraft_name"
    # 用 /tell 私訊玩家。如果想全頻廣播就改成 /say
    try:
        response = _rcon_send(f"tell {player_name} {message}")
    except (MCRconException, ConnectionError, OSError) as e:
        _rcon_logger.warning("RCON tell 失敗: %s", e)
        return False, f"RCON error: {e}"
    failed_markers = ("No player", "Unknown", "Incorrect", "Expected")
    if any(m in response for m in failed_markers):
        return False, response
    return True, response


def deliver_cart_to_player(user_account, cart_items):
    """
    結帳時呼叫,直接把購物車裡每個品項 /give 給玩家。
    cart_items 格式: [{'mc_item_id': 'minecraft:diamond', 'quantity': 64}, ...]
    回傳: (ok: bool, message: str, details: list)
      - ok=True 表示全部發送成功,可建立訂單
      - ok=False 表示玩家不在線或部分失敗,結帳路由應拒絕並回覆使用者
    """
    player_name = get_user_minecraft_name(user_account)
    if not player_name:
        return False, "尚未綁定 Minecraft 角色名", []

    # 先確認玩家在線,離線就直接擋下
    if not rcon_is_player_online(player_name):
        return False, f"玩家 {player_name} 不在線上,請先進入遊戲再購買", []

    details = []
    all_ok = True
    for item in cart_items:
        mc_item_id = item.get('mc_item_id')
        if not mc_item_id:
            details.append({'item': item, 'ok': False, 'msg': '商品未設定 mc_item_id'})
            all_ok = False
            continue
        ok, response = rcon_give_item(
            player_name=player_name,
            item_id=mc_item_id,
            quantity=item['quantity'],
        )
        details.append({'item': item, 'ok': ok, 'msg': response})
        if not ok:
            all_ok = False

    return all_ok, "OK" if all_ok else "部分發送失敗", details

# ── Branch D：商品管理（後台） ────────────────────────────────────────────────

# 新增商品，預設為上架狀態，回傳新商品的 id
# mc_item_id 為選填，填入 Minecraft 道具 ID（例如 minecraft:diamond）
# 若為序號類商品則不填，預設為 None
@db_transaction
def add_product(cursor, name, original_price, sale_price, description, img_filename, mc_item_id):
    # 新增商品，預設為上架狀態，回傳新商品的 id
    cursor.execute(f"""
        INSERT INTO `{BRANCH_B_PRODUCTS_TABLE}`
        (`mc_item_id`, `name`, `original_price`, `sale_price`, `description`, `product_pic`, `is_active`)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (mc_item_id, name, original_price, sale_price, description, img_filename))
    #     ↑ 順序改為與欄位一致
    return cursor.lastrowid

@db_transaction
def add_product_stock(cursor, product_id, quantity):
    # 為商品建立庫存紀錄（商品入庫）
    cursor.execute("""
        INSERT INTO `product_stock` (product_id, product_quantity)
        VALUES (?, ?)
    """, (product_id, quantity))

@db_transaction
def set_product_stock(cursor, product_id, quantity):
    # 直接把商品庫存設為指定數量(修改商品時使用)。
    # 若該商品還沒有庫存紀錄,自動建立一筆;否則更新。
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
    # 設定商品上下架狀態，is_active=1 為上架，0 為下架
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
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
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET {set_sql}
        WHERE `id` = ?
    """, set_value + (product_id,))

@db_transaction
def get_all_products(cursor):
    # 取得所有未刪除的商品清單（含庫存），供後台管理頁使用
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
    # 軟刪除商品，將 is_deleted 設為 1，資料不實際移除
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
        SET is_deleted = 1
        WHERE id = ?
    """, (product_id,))

@db_transaction
def add_log(cursor, admin_account, action, product_id, product_name):
    # 新增一筆後台操作記錄
    cursor.execute("""
        INSERT INTO manage_log
        (admin_account, action, product_id, product_name)
        VALUES (?, ?, ?, ?)
    """, (admin_account, action, product_id, product_name))

@db_transaction
def get_logs(cursor):
    # 取得所有後台操作記錄，依時間降冪排列
    cursor.execute("""
        SELECT * FROM manage_log
        ORDER BY created_at DESC
    """)
    return cursor.fetchall()

@db_transaction
def restore_product(cursor, product_id):
    # 還原已軟刪除的商品
    cursor.execute(f"""
        UPDATE `{BRANCH_B_PRODUCTS_TABLE}`
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
def clear_default_cards(cursor, user_account):
    """
    把該會員所有卡片設為非預設。
    """
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 0
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (user_account,)
    )

@db_transaction
def set_default_card(cursor, user_account, card_id):
    """
    把指定卡片設為預設卡。
    """
    cursor.execute(
        f"""UPDATE `member_cards`
            SET is_default = 1
            WHERE id = ?
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = ?)""",
        (card_id, user_account)
    )

# ── manage_log 報表(管理頁日誌,按月份分組) ─────────────────────────────────

@db_transaction
def get_log_months(cursor):
    """
    取得 manage_log 中有紀錄的月份清單,以及每個月的筆數。
    回傳格式: [{"month": "2025-11", "log_count": 8}, ...]
    """
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
    """
    取得指定月份(格式 YYYY-MM)的所有日誌紀錄,依時間降冪排列。
    """
    cursor.execute("""
        SELECT created_at, admin_account, action, product_id, product_name
        FROM manage_log
        WHERE DATE_FORMAT(created_at, '%Y-%m') = ?
        ORDER BY created_at DESC
    """, (month,))
    return cursor.fetchall()


# ── 已完成訂單查詢(報表/篩選用) ─────────────────────────────────────────────

@db_transaction
def get_user_accounts_with_orders(cursor):
    """取得有過訂單(含已完成的)的所有使用者帳號清單,給管理員下拉用。"""
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
    """
    篩選「已完成」訂單。
    user_account:None=管理員模式撈全部;傳帳號=只撈該人(使用者模式)
    target_user :管理員可指定要看哪個使用者(None=全部使用者)
    month       :YYYY-MM 格式
    min_total/max_total:金額範圍
    """
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
        # 使用者模式:強制只看自己
        sql += " AND u.user_account = ?"
        params.append(user_account)
    elif target_user:
        # 管理員指定看某人
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
    """
    取得訂單明細(含商品名稱/圖片)。
    user_account=None : 管理員模式,不檢查擁有者
    user_account=帳號 : 使用者模式,訂單必須屬於該人,否則回 None
    """
    if user_account is not None:
        # 先驗證訂單屬於這個人
        cursor.execute(f"""
            SELECT 1 FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
            WHERE o.id = ? AND u.user_account = ? AND o.status = '已完成'
        """, (order_id, user_account))
        if not cursor.fetchone():
            return None  # 不是你的訂單 / 訂單不存在 / 不是已完成
    else:
        # 管理員只要驗證訂單存在且已完成
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
