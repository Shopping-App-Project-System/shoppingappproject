"""訂單與金流狀態。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import (
    BRANCH_A_TABLE,
    BRANCH_B_PRODUCTS_TABLE,
    BRANCH_C_ORDER_TABLE,
    BRANCH_C_ORDER_ITEMS_TABLE,
)


@db_transaction
def insert_order(cursor, user_account, total, payment_method, note,
                 status='已完成', ecpay_trade_no=None):
    """
    建立新訂單。

    【狀態流程說明】
    - 預設 status='已完成'（向後相容原本「下單即完成」的設計）
    - 走綠界刷卡時改傳 status='待付款'，等綠界跳回 /payment/ecpay/return 才更新為「已完成」

    【相依功能注意事項】
    由於既有的營收報表都用 WHERE status = '已完成' 過濾，
    '待付款' / '付款失敗' 訂單不會被算進營收，不會破壞既有統計。

    :param user_account: 下單會員的帳號
    :param total: 訂單總金額
    :param payment_method: 付款方式
    :param note: 訂單備註
    :param status: 訂單初始狀態（預設「已完成」；綠界訂單請傳「待付款」）
    :param ecpay_trade_no: 綠界 MerchantTradeNo（可選；走綠界才有）
    :return: 新建立訂單的 id
    """
    cursor.execute(
        f'''INSERT INTO `{BRANCH_C_ORDER_TABLE}`
            (user_id, total, payment_method, note, status, ecpay_trade_no)
            VALUES ((SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s),%s,%s,%s,%s,%s)''',
        (user_account, total, payment_method, note, status, ecpay_trade_no)
    )
    return cursor.lastrowid


@db_transaction
def get_order_by_ecpay_trade_no(cursor, ecpay_trade_no):
    """
    依綠界 MerchantTradeNo 查訂單。
    callback 回來時用這個查單。

    :return: 訂單 row（含 id, user_id, total, status, ecpay_trade_no...）, 找不到回 None
    """
    cursor.execute(
        f'''SELECT o.id, o.user_id, o.total, o.status, o.ecpay_trade_no,
                   u.user_account
            FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
            WHERE o.ecpay_trade_no = %s''',
        (ecpay_trade_no,)
    )
    return cursor.fetchone()


@db_transaction
def update_order_payment_status(cursor, order_id, status, ecpay_rtn_code=None):
    """
    更新訂單狀態（綠界 callback 回來時呼叫）。

    :param order_id: 訂單 id
    :param status: 新狀態（'已完成' / '付款失敗'）
    :param ecpay_rtn_code: 綠界回傳代碼（1=成功，其他=失敗訊息）
    """
    cursor.execute(
        f'''UPDATE `{BRANCH_C_ORDER_TABLE}`
            SET status = %s, ecpay_rtn_code = %s
            WHERE id = %s''',
        (status, ecpay_rtn_code, order_id)
    )


@db_transaction
def get_order_status(cursor, order_id, user_account):
    """
    使用者進付款結果頁時，查自己的訂單狀態。
    限本人查詢（避免有人改 URL 看別人的訂單）。
    """
    cursor.execute(
        f'''SELECT o.id, o.total, o.status, o.payment_method, o.created_at,
                   o.ecpay_trade_no, o.ecpay_rtn_code
            FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
            WHERE o.id = %s AND u.user_account = %s''',
        (order_id, user_account)
    )
    return cursor.fetchone()


@db_transaction
def get_user_order_seq(cursor, user_account, order_id):
    cursor.execute(f"""
        SELECT COUNT(*) as seq
        FROM `{BRANCH_C_ORDER_TABLE}` o
        JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
        WHERE u.user_account = %s AND o.status = '已完成' AND o.id <= %s
    """, (user_account, order_id))
    return cursor.fetchone()['seq']


@db_transaction
def insert_order_item(cursor, order_id, product_id, quantity, price):
    # 新增一筆訂單明細，記錄下單當下的價格
    cursor.execute(
        f'INSERT INTO `{BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)',
        (order_id, product_id, quantity, price)
    )
    return cursor.lastrowid


@db_transaction
def get_order_items(cursor, order_id):
    # 取得指定訂單的所有商品明細（商品 id 與數量），取消訂單補回庫存時使用
    cursor.execute(
        f'SELECT product_id, quantity FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` WHERE order_id = %s',
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
            WHERE oi.order_id = %s''',
        (order_id,)
    )
    return cursor.fetchall()


@db_transaction
def get_all_orders(cursor, user_account):
    # 取得該會員所有訂單（含已取消），依建立時間升冪排列
    cursor.execute(
        f'''SELECT id, total, payment_method, note, status, created_at
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)
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
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)
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
            WHERE user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)
            AND status != '已取消'
            AND status LIKE %s
            ORDER BY created_at DESC''',
        (user_account, like_keyword)
    )
    return cursor.fetchall()


@db_transaction
def get_order(cursor, order_id, user_account):
    """
    取得指定訂單，供「取消訂單」流程做權限與狀態驗證。

    【驗證條件】
    1. 訂單 id 存在
    2. 訂單必須屬於本人（user_account 對應的 user_id）
    3. 訂單狀態不能是「已取消」（已取消的不能再取消一次）

    【為何放寬狀態限制】
    原本此處限制狀態必須為「處理中」才允許取消，但因 insert_order 已調整為
    下單後直接寫入「已完成」，若沿用舊限制將導致使用者永遠無法取消任何訂單。
    因此改為：只要訂單不是「已取消」狀態，皆允許取消，
    以保留使用者在「已完成」狀態下仍可取消訂單的權益。

    :param order_id: 訂單 id
    :param user_account: 操作者帳號（必須為訂單擁有者）
    :return: 符合條件的訂單列，否則為 None
    """
    cursor.execute(
        f'''SELECT id FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE id = %s
            AND user_id = (SELECT id FROM `{BRANCH_A_TABLE}` WHERE user_account = %s)
            AND status != '已取消' ''',
        (order_id, user_account)
    )
    return cursor.fetchone()


@db_transaction
def cancel_order(cursor, order_id):
    # 將指定訂單狀態更新為「已取消」
    cursor.execute(
        f"UPDATE `{BRANCH_C_ORDER_TABLE}` SET status = '已取消' WHERE id = %s",
        (order_id,)
    )
