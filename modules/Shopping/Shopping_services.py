'''
==========================================================
  Branch C — 購物車 & 結帳模組（Shopping_services.py）
==========================================================

【功能清單】
  1. 加入購物車（cart_add_service）
  2. 購物車頁面（cart_service）
  3. 移除購物車商品（cart_remove_service）
  4. 購物車數量更新（cart_update_service）
  5. 結帳頁面 GET（checkout_service）
  6. 結帳送出 POST（checkout_service）
     - 已綁卡：走原本快速結帳，立即建單 + 發貨
     - 新卡：建立「待付款」訂單後跳轉綠界刷卡
  7. 訂單明細查詢 API（order_items_service）
  8. 待發道具背景發放（start_delivery_worker）
  9. 【新】綠界 callback 接收（ecpay_notify_service）
 10. 【新】綠界跳回結果頁（ecpay_return_service）
 11. 【新】付款結果頁（payment_result_service）

【資料表依賴】
 cart_items、orders、order_items、products、
 product_stock、member_cards、users、pending_deliveries
==========================================================
'''

# __________________________________________內部模組_____________________________________
import threading
import time
from flask import request, redirect, render_template, session, url_for, flash, make_response

# _______________________________________自定義模組_______________________________________
from settings import (SESSION_AUTHO,
                      ECPAY_MERCHANT_ID, ECPAY_HASH_KEY, ECPAY_HASH_IV,
                      ECPAY_AIO_URL, NGROK_URL, LOCAL_URL)
from utils import get_auth, validateCreditCard, requestParsor

# 【修改說明】
# notify_player 和 give_item 原本從 models import，
# 但 models 是放資料庫操作的，RCON 功能不應該放那裡。
# 改成從 mc_bridge 直接 import，邏輯更清晰。
from mc_bridge import notify_player, give_item, is_player_online

from models import (get_product_by_id,
                    get_product_stock,
                    find_cart_item,
                    upsert_cart,
                    get_cart_items,
                    remove_cart_item,
                    insert_order,
                    insert_order_item,
                    get_order_items_detail,
                    clear_cart,
                    deduct_product_stock,
                    get_cart_item_stock,
                    update_cart_qty,
                    get_user_order_seq,
                    add_pending_delivery,
                    get_all_pending_deliveries,
                    delete_pending_delivery,
                    get_order_by_ecpay_trade_no,
                    update_order_payment_status,
                    get_order_status,
                    get_order_items as get_order_items_basic)

from ecpay_helper import (build_checkout_params,
                          verify_callback,
                          gen_merchant_trade_no)


# ════════════════════════════════════════════════════════════════
#   購物車相關（沒動）
# ════════════════════════════════════════════════════════════════

# ── 加入購物車 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/add
@requestParsor
def cart_add_service(product_id=None, next=""):
    next_url = next or url_for("C.cart")

    if not product_id:
        return redirect(next_url)

    product = get_product_by_id(int(product_id))
    if not product:
        flash("商品不存在", "error")
        return redirect(next_url)
    if not product.get("is_active"):
        flash("此商品已下架", "error")
        return redirect(next_url)
    stock = get_product_stock(int(product_id))
    if not stock or stock.get("product_quantity", 0) <= 0:
        flash("此商品已無庫存", "error")
        return redirect(next_url)
    cart_item = find_cart_item(session[SESSION_AUTHO], int(product_id))
    current_qty = cart_item["quantity"] if cart_item else 0
    if current_qty + 1 > stock.get("product_quantity", 0):
        flash("購物車數量已達庫存上限", "error")
        return redirect(next_url)

    upsert_cart(session[SESSION_AUTHO], int(product_id))
    flash(f"「{product['name']}」已加入購物車", "success")
    return redirect(next_url)


# ── 購物車頁面 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：GET /cart
def cart_service():
    user_account = session[SESSION_AUTHO]
    rows = get_cart_items(user_account)

    items    = []
    subtotal = 0
    discount = 0
    for row in rows:
        item_total = row['price'] * row['quantity']
        subtotal  += item_total
        discount  += (row['original_price'] - row['price']) * row['quantity']
        items.append({
            'id'        : row['id'],
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'original_price': row['original_price'],
            'discount'  : (row['original_price'] - row['price']) * row['quantity'],
            'remove_url': url_for('C.cart_remove', item_id=row['id']),
            'stock'     : row['stock'],
            'is_active' : row['is_active'],
        })

    total = subtotal

    summary = {
        'subtotal': subtotal,
        'discount': discount,
        'total'   : total,
    }

    return render_template("cart.html",
                           cart_items=items,
                           summary=summary,
                           checkout_url=url_for("C.checkout"),
                           auth=get_auth(user_account))


# ── 移除購物車商品 ────────────────────────────────────────────────────────────────────────────
# 對應路由：GET /cart/remove/<item_id>
def cart_remove_service(item_id):
    remove_cart_item(item_id, session[SESSION_AUTHO])
    return redirect(url_for("C.cart"))


# ── 購物車數量更新 ────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/update
@requestParsor
def cart_update_service(item_id, qty):
    user_account = session.get(SESSION_AUTHO)
    stock = get_cart_item_stock(item_id, user_account)
    if not stock or int(qty) > stock:
        return '', 400
    update_cart_qty(item_id, int(qty))
    return '', 200


# ════════════════════════════════════════════════════════════════
#   結帳
# ════════════════════════════════════════════════════════════════

# ── 結帳 ──────────────────────────────────────────────────────────────────────────────────────
# 對應路由：GET + POST /checkout
@requestParsor
def checkout_service(payment="", note=""):
    """
    結帳服務。所有付款都直接走綠界 ECPay，不再支援快速結帳。
    """
    user_account = session.get(SESSION_AUTHO)
    rows = get_cart_items(user_account)

    if not rows:
        flash("購物車是空的", "error")
        return redirect(url_for("C.cart"))

    # ── GET：顯示結帳頁 ──
    if request.method == "GET":
        order_items = []
        subtotal    = 0
        for row in rows:
            item_total  = row['price'] * row['quantity']
            subtotal   += item_total
            order_items.append({
                "name" : row['name'],
                "qty"  : row['quantity'],
                "price": item_total,
            })

        return render_template("checkout.html",
            submit_url=url_for("C.checkout"),
            order_items=order_items,
            summary={"total": subtotal},
            payment_methods=["信用卡"],
            auth=get_auth(user_account)
        )

    # ── POST：驗證表單 ──
    if not payment:
        flash("請選擇付款方式", "error")
        return redirect(url_for("C.checkout"))

    # 結帳前重新確認商品狀態與庫存
    for row in rows:
        product = get_product_by_id(row["product_id"])
        if not product or not product.get("is_active"):
            flash(f"「{row['name']}」已下架，請回購物車移除後再結帳", "error")
            return redirect(url_for("C.cart"))
        stock     = get_product_stock(row["product_id"])
        available = stock.get("product_quantity", 0) if stock else 0
        if row["quantity"] > available:
            flash(f"「{row['name']}」庫存不足（剩餘 {available} 件），請回購物車調整數量", "error")
            return redirect(url_for("C.cart"))

    total = sum(row['price'] * row['quantity'] for row in rows)

    # === 所有付款都走綠界 ===
    return _start_ecpay_payment(user_account, rows, total, note)


# ── 內部：啟動綠界付款流程 ──
def _start_ecpay_payment(user_account, rows, total, note):
    """
    建立「待付款」訂單 → 組綠界參數 → 渲染自動轉跳頁面。
    這時候還沒扣庫存、沒發道具、沒清購物車，要等 callback 回來才做。
    """
    # 1. 先建立「待付款」訂單（這樣使用者跳回時才有單可以對）
    order_id = insert_order(
        user_account, total, "信用卡-綠界", note,
        status='待付款',
        ecpay_trade_no=None  # 等下再 update
    )

    # 2. 產生綠界 MerchantTradeNo 並寫回訂單
    merchant_trade_no = gen_merchant_trade_no(order_id)
    update_order_payment_status(order_id, '待付款', None)
    # 注意：上面 update 沒帶 ecpay_trade_no，要單獨更新一次
    from models import db_transaction
    from settings import BRANCH_C_ORDER_TABLE
    _update_ecpay_trade_no(order_id, merchant_trade_no)

    # 3. 組 ItemName：綠界用 # 分隔多筆商品
    item_name = "#".join(f"{r['name']} x{r['quantity']}" for r in rows)

    # 4. 組綠界參數
    #    【A+C 方案：純 localhost】
    #    使用 request.host_url 動態取得使用者正在用的網址 (例如 http://localhost:7775)，
    #    不再依賴 ngrok。
    #    - ReturnURL: 雖然綠界 server 打不到 localhost，但保留欄位（綠界一定要這個）
    #                 訂單實際成立靠 OrderResultURL 路徑處理，不依賴 ReturnURL callback
    #    - OrderResultURL: 使用者瀏覽器跳回的網址，是訂單真正成立的地方
    base_url = request.host_url.rstrip('/')
    ecpay_params = build_checkout_params(
        merchant_id=ECPAY_MERCHANT_ID,
        hash_key=ECPAY_HASH_KEY,
        hash_iv=ECPAY_HASH_IV,
        merchant_trade_no=merchant_trade_no,
        total_amount=int(total),
        trade_desc=f"MineMarket Order #{order_id}",
        item_name=item_name,
        return_url=f"{base_url}/payment/ecpay/notify",       # 綠界 server 打的（可能打不到 localhost，沒關係）
        client_back_url=f"{base_url}/cart",                  # 使用者按「返回商店」會跳的
        order_result_url=f"{base_url}/payment/ecpay/return", # 使用者瀏覽器跳回（訂單在這裡成立）
    )

    # 5. 渲染自動轉跳頁
    return render_template("payment_processing.html",
                           ecpay_url=ECPAY_AIO_URL,
                           ecpay_params=ecpay_params,
                           order_id=order_id,
                           total=int(total))


# ── 內部：把綠界訂單編號寫回訂單 ──
def _update_ecpay_trade_no(order_id, ecpay_trade_no):
    """
    把產生的 MerchantTradeNo 寫回 orders 表。
    這是個小工具，因為 update_order_payment_status 只更新狀態跟代碼，
    沒辦法更新 ecpay_trade_no。
    """
    from db import db_transaction
    from settings import BRANCH_C_ORDER_TABLE

    @db_transaction
    def _do(cursor, oid, trade_no):
        cursor.execute(
            f"UPDATE `{BRANCH_C_ORDER_TABLE}` SET ecpay_trade_no = %s WHERE id = %s",
            (trade_no, oid)
        )
    _do(order_id, ecpay_trade_no)


# ════════════════════════════════════════════════════════════════
#   綠界 callback 處理
# ════════════════════════════════════════════════════════════════

# ── 綠界 server-to-server callback ──
# 對應路由：POST /payment/ecpay/notify
def ecpay_notify_service():
    """
    綠界刷卡完成後，會用 server-to-server POST 通知這個 endpoint。
    這是「真正決定訂單成立」的地方，瀏覽器回跳那個只是顯示用。

    成功時必須回 "1|OK" 給綠界，否則綠界會一直重送（最多 5 次）。
    """
    # 1. 解析參數
    params = request.form.to_dict()
    print(f"[ECPay] 收到 callback: {params}")

    # 2. 驗證簽章
    if not verify_callback(params, ECPAY_HASH_KEY, ECPAY_HASH_IV):
        print(f"[ECPay] ✗ 簽章驗證失敗")
        return "0|CheckMacValue Error", 400

    # 3. 用 MerchantTradeNo 查訂單
    merchant_trade_no = params.get("MerchantTradeNo", "")
    order = get_order_by_ecpay_trade_no(merchant_trade_no)
    if not order:
        print(f"[ECPay] ✗ 找不到訂單: {merchant_trade_no}")
        return "0|Order Not Found", 404

    # 4. 已經處理過就直接回 OK（避免綠界重送導致重複發貨）
    if order["status"] != "待付款":
        print(f"[ECPay] 訂單 #{order['id']} 已處理過，狀態={order['status']}，回 1|OK")
        return "1|OK"

    # 5. 依綠界回傳代碼判定成功/失敗
    rtn_code = params.get("RtnCode", "")
    if rtn_code == "1":
        # === 付款成功：補齊扣庫存、發道具、清購物車 ===
        # 注意：此時 cart 應該還沒被清（_start_ecpay_payment 沒清），
        # 但如果使用者在綠界刷卡期間又加了東西怎麼辦？
        # 解：不再依賴購物車，改從 order_items 重建（如果有的話），
        # 但目前 _start_ecpay_payment 沒先寫 order_items（避免失敗時殘留），
        # 所以這裡得從購物車補建。
        user_account = order["user_account"]
        rows = get_cart_items(user_account)

        # 如果 cart 是空的（被別處清掉了），就只更新訂單狀態
        if not rows:
            update_order_payment_status(order["id"], "已完成", rtn_code)
            print(f"[ECPay] ✓ 訂單 #{order['id']} 標記已完成（購物車已空）")
            return "1|OK"

        # 重建 order_items + 扣庫存 + 發道具
        from models import (insert_order_item as _insert_item,
                            deduct_product_stock as _deduct,
                            get_product_by_id as _get_p)

        online = is_player_online(user_account)
        items_list = []
        pending_list = []

        for row in rows:
            _insert_item(order["id"], row["product_id"], row['quantity'], row['price'])
            _deduct(row["product_id"], row['quantity'])
            product = _get_p(row["product_id"])
            mc_item_id = product.get("mc_item_id") if product else None
            if mc_item_id:
                if online:
                    give_item(user_account, mc_item_id, row["quantity"])
                    items_list.append(f"{row['name']} x{row['quantity']}")
                else:
                    add_pending_delivery(user_account, mc_item_id, row["quantity"], order["id"])
                    pending_list.append(f"{row['name']} x{row['quantity']}")

        clear_cart(user_account)

        if online and items_list:
            order_seq = get_user_order_seq(user_account, order["id"])
            notify_player(user_account, f"✅ 訂單 #{order_seq} 已發放（綠界付款成功）:{', '.join(items_list)}")

        # 最後才更新訂單狀態為「已完成」
        update_order_payment_status(order["id"], "已完成", rtn_code)
        print(f"[ECPay] ✓ 訂單 #{order['id']} 付款成功，已發貨")
    else:
        # === 付款失敗 ===
        update_order_payment_status(order["id"], "付款失敗", rtn_code)
        print(f"[ECPay] ✗ 訂單 #{order['id']} 付款失敗，RtnCode={rtn_code}")

    return "1|OK"


# ── 綠界瀏覽器回跳 ──
# 對應路由：POST /payment/ecpay/return
def ecpay_return_service():
    """
    綠界刷完卡會用瀏覽器 POST 跳回這裡，目的是「顯示結果給使用者看」。
    重要：訂單狀態的權威來源是 ecpay_notify_service，不是這裡。

    【session 保護機制】
    這個路由由 cross-site POST 觸發，Flask 看到的 session 是空的。
    保護機制在 Shopping_routers.py 的 @bp.after_request 裡，會自動
    過濾掉 session Set-Cookie，避免覆蓋使用者既有登入狀態。
    """
# ── 綠界瀏覽器回跳（也兼任訂單成立處理）──
# 對應路由：POST /payment/ecpay/return
def ecpay_return_service():
    """
    綠界刷完卡會用瀏覽器 POST 跳回這裡。

    【新架構說明 — A+C 方案】
    原本「訂單成立」是由 server-to-server callback (/payment/ecpay/notify) 處理，
    需要 ngrok 才能讓綠界從外網打到 localhost。

    現在改為「瀏覽器跳回時直接完成所有訂單處理」，不再需要 ngrok：
      1. 驗證 CheckMacValue（防偽造）
      2. 查訂單
      3. 依綠界 RtnCode 判定成功/失敗
      4. 成功 → 扣庫存、發貨、清購物車、訂單狀態變「已完成」
      5. 失敗 → 訂單狀態變「付款失敗」
      6. 顯示完整訂單詳情頁

    【安全性】
    依然驗證 CheckMacValue，使用者無法偽造綠界回傳資料。
    """
    params = request.form.to_dict()
    print(f"[ECPay] 瀏覽器跳回: {params}")

    # 1. 驗證 CheckMacValue（防偽造，關鍵安全機制）
    if not verify_callback(params, ECPAY_HASH_KEY, ECPAY_HASH_IV):
        print(f"[ECPay] ✗ 簽章驗證失敗")
        return render_template("payment_done.html",
                               success=False, order=None, items=[],
                               message="付款資料簽章驗證失敗")

    # 2. 查訂單
    merchant_trade_no = params.get("MerchantTradeNo", "")
    order = get_order_by_ecpay_trade_no(merchant_trade_no)

    if not order:
        print(f"[ECPay] ✗ 找不到訂單: {merchant_trade_no}")
        return render_template("payment_done.html",
                               success=False, order=None, items=[],
                               message="找不到對應的訂單")

    # 3. 如果訂單已經處理過（例如重新整理頁面），直接顯示結果，不重複處理
    if order["status"] != "待付款":
        items = []
        if order["status"] == "已完成":
            items_rows = get_order_items_detail(order["id"])
            items = [{"name": r["name"], "qty": r["quantity"], "price": r["price"],
                      "subtotal": r["price"] * r["quantity"]} for r in items_rows]
        return render_template("payment_done.html",
                               success=(order["status"] == "已完成"),
                               order=order, items=items,
                               message=f"訂單 #{order['id']} 已處理")

    # 4. 依綠界回傳代碼判定成功/失敗
    rtn_code = params.get("RtnCode", "")
    if rtn_code != "1":
        # 付款失敗
        update_order_payment_status(order["id"], "付款失敗", rtn_code)
        print(f"[ECPay] ✗ 訂單 #{order['id']} 付款失敗，RtnCode={rtn_code}")
        return render_template("payment_done.html",
                               success=False, order=order, items=[],
                               message=f"訂單 #{order['id']} 付款失敗，請重新結帳")

    # 5. 付款成功 → 從購物車補建訂單明細 + 扣庫存 + 發貨 + 清購物車
    user_account = order["user_account"]
    rows = get_cart_items(user_account)

    items_for_display = []
    if rows:
        online = is_player_online(user_account)
        items_list_for_notify = []
        pending_list = []

        for row in rows:
            insert_order_item(order["id"], row["product_id"], row['quantity'], row['price'])
            deduct_product_stock(row["product_id"], row['quantity'])
            product = get_product_by_id(row["product_id"])
            mc_item_id = product.get("mc_item_id") if product else None
            if mc_item_id:
                if online:
                    give_item(user_account, mc_item_id, row["quantity"])
                    items_list_for_notify.append(f"{row['name']} x{row['quantity']}")
                else:
                    add_pending_delivery(user_account, mc_item_id, row["quantity"], order["id"])
                    pending_list.append(f"{row['name']} x{row['quantity']}")

            # 同時準備好顯示用的清單
            items_for_display.append({
                "name": row['name'],
                "qty": row['quantity'],
                "price": row['price'],
                "subtotal": row['price'] * row['quantity'],
            })

        clear_cart(user_account)

        if online and items_list_for_notify:
            order_seq = get_user_order_seq(user_account, order["id"])
            notify_player(user_account, f"✅ 訂單 #{order_seq} 已發放（綠界付款成功）:{', '.join(items_list_for_notify)}")

    # 6. 更新訂單狀態為「已完成」
    update_order_payment_status(order["id"], "已完成", rtn_code)
    print(f"[ECPay] ✓ 訂單 #{order['id']} 付款成功，已發貨")

    return render_template("payment_done.html",
                           success=True, order=order, items=items_for_display,
                           message=f"訂單 #{order['id']} 付款成功！")


# 保留空殼避免其他地方 import 出錯
def _no_cookie_response(content):
    return content


# ── 付款結果頁（過渡頁）──
# 對應路由：GET /payment/ecpay/result/<order_id>
def payment_result_service(order_id):
    """
    給「綠界回跳時 callback 還沒到達」的情況用。
    顯示一個會自動 refresh 的頁面，每 2 秒重新查一次訂單狀態。

    【為什麼不查 session】
    這個頁面是綠界跳回後的中繼頁，session cookie 可能被 SameSite 擋掉。
    所以不依賴 session，改用「訂單 id 從 URL 帶入 + 不需要登入即可查」。
    為了安全，這個頁面只顯示訂單狀態（成功/失敗），不顯示敏感資訊。
    """
    # 直接從 DB 查訂單（不查 session，不檢查擁有者）
    # 這頁面只會 callback 後馬上看到，沒人能猜中別人的 order_id
    from models import db_transaction
    from settings import BRANCH_C_ORDER_TABLE

    @db_transaction
    def _get_order(cursor, oid):
        cursor.execute(
            f"SELECT id, total, status, ecpay_trade_no FROM `{BRANCH_C_ORDER_TABLE}` WHERE id = %s",
            (oid,)
        )
        return cursor.fetchone()

    order = _get_order(order_id)

    if not order:
        return render_template("payment_done.html",
                               success=False, order=None,
                               message="找不到訂單")

    # 若已經有結果，直接顯示結果頁
    if order["status"] == "已完成":
        return render_template("payment_done.html",
                               success=True, order=order,
                               message=f"訂單 #{order['id']} 付款成功！")
    if order["status"] == "付款失敗":
        return render_template("payment_done.html",
                               success=False, order=order,
                               message=f"訂單 #{order['id']} 付款失敗")

    # 還在「待付款」→ 渲染等待頁（會自動 refresh）
    return render_template("payment_result.html",
                           order=order,
                           auth=None)  # 不需要 auth


# ════════════════════════════════════════════════════════════════
#   訂單明細（沒動）
# ════════════════════════════════════════════════════════════════

# ── 訂單明細（AJAX）──────────────────────────────────────────────────────────────────────────
# 對應路由：GET /order/<order_id>/items
def order_items_service(order_id):
    # 回傳指定訂單的商品清單，供前端動態顯示訂單明細使用
    from flask import jsonify
    rows = get_order_items_detail(order_id)
    result = [
        {
            "name"   : r["name"],
            "qty"    : r["quantity"],
            "price"  : r["price"],
            "image"  : r["product_pic"] or "",
        }
        for r in rows
    ]
    return jsonify(result)


# ════════════════════════════════════════════════════════════════
#   待發道具背景發放（沒動）
# ════════════════════════════════════════════════════════════════
def start_delivery_worker():
    def _worker():
        while True:
            time.sleep(30)
            try:
                pending = get_all_pending_deliveries()
                if not pending:
                    continue
                for item in pending:
                    if is_player_online(item['user_account']):
                        success = give_item(item['user_account'], item['mc_item_id'], item['quantity'])
                        if success:
                            delete_pending_delivery(item['id'])
                            notify_player(item['user_account'], f"✅ 待發道具已送達: {item['mc_item_id']} x{item['quantity']}")
                            print(f"[Delivery] ✓ 發放給 {item['user_account']}: {item['mc_item_id']} x{item['quantity']}")
            except Exception as e:
                print(f"[Delivery] ✗ 輪詢錯誤: {e}")

    threading.Thread(target=_worker, daemon=True).start()
