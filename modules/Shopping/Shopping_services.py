'''
==========================================================
  Branch C — 購物車 & 結帳模組（Shopping_services.py）
==========================================================

【功能清單】
  1. 加入購物車（cart_add_service）
     - 驗證商品是否存在、是否已下架、是否有庫存
     - 檢查購物車現有數量 + 1 是否超過庫存上限
     - 通過驗證後寫入購物車，數量重複加購時自動累加

  2. 購物車頁面（cart_service）
     - 列出該會員所有購物車商品
     - 計算每項小計（單價 × 數量）、運費（有商品才收 $60）、
       折扣、總金額
     - 顯示每項商品的剩餘庫存與上下架狀態
     - 下架商品顯示「已下架」標籤並停用數量調整按鈕
     - 購物車為空時顯示空狀態提示

  3. 移除購物車商品（cart_remove_service）
     - 從購物車刪除指定商品（驗證商品屬於本人）

  4. 購物車數量更新（cart_update_service）
     - 即時更新購物車商品數量
     - 驗證數量不超過庫存上限

  5. 結帳頁面 GET（checkout_service）
     - 顯示結帳表單，自動帶入使用者姓名、手機、地址
     - 列出購物車商品明細與金額摘要
     - 顯示該會員已儲存的信用卡供快速選擇
     - 若尚未綁定信用卡，選擇信用卡付款時顯示警告說明

  6. 結帳送出 POST（checkout_service）
     - 必填驗證：收件人姓名、地址、付款方式、配送方式
     - 手機格式驗證（09 開頭 10 碼）
     - 信用卡驗證：
        · 已儲存的卡：驗證 card_id 確實屬於本人
        · 手動輸入：驗證 16 碼格式，記錄後四碼
     - 結帳前驗證商品是否已下架，給出明確的「已下架」錯誤訊息
     - 結帳前再次驗證庫存（防止購物車舊資料導致超量）
     - 後端重新計算總金額（防止前端竄改）
     - 建立訂單與訂單明細，扣減各商品庫存，清空購物車

  7. 取消訂單（order_cancel_service）
     - 驗證訂單屬於本人且狀態為「處理中」
     - 更新狀態為「已取消」
     - 自動將該訂單所有商品的庫存補回

  8. 訂單明細查詢 API（order_items_service）
     - 對應路由：GET /order/<order_id>/items
     - 回傳指定訂單的商品清單（名稱、數量、單價、圖片）
     - 回傳格式：JSON 陣列，供前端動態顯示訂單明細使用

【資料表依賴】
 cart_items、orders、order_items、products、
 product_stock、member_cards、users
==========================================================
'''

# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash


# _______________________________________自定義模組_______________________________________
from settings import SESSION_AUTHO
from utils import get_auth,validateMobile,validateCreditCard,requestParsor,getVerifyToken
from mc_bridge import notify_player, give_item
from models import (getUser,
                    get_product_by_id,
                    get_product_stock,
                    find_cart_item,
                    upsert_cart,
                    get_cart_items,
                    remove_cart_item,
                    insert_order,
                    insert_order_item,
                    get_order_items,
                    get_order_items_detail,
                    clear_cart,
                    get_order,
                    cancel_order,
                    get_member_cards,
                    deduct_product_stock,
                    restore_product_stock,
                    get_cart_item_stock,
                    update_cart_qty,
                    update_order_item_serial,
                    get_order_item_by_serial,
                    redeem_serial)


# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________

# ── 加入購物車 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/add
@requestParsor
def cart_add_service(product_id=None, next=""):
    next_url = next or url_for("C.cart")

    if not product_id:                  # 表單沒有帶 product_id，無法處理，直接導回
        return redirect(next_url)

    product = get_product_by_id(int(product_id))
    if not product:                     # 資料庫找不到此商品
        flash("商品不存在", "error")
        return redirect(next_url)
    if not product.get("is_active"):    # 商品存在但已被下架
        flash("此商品已下架", "error")
        return redirect(next_url)
    stock = get_product_stock(int(product_id))
    if not stock or stock.get("product_quantity", 0) <= 0:  # 庫存為 0 或無庫存紀錄
        flash("此商品已無庫存", "error")
        return redirect(next_url)
    cart_item = find_cart_item(session[SESSION_AUTHO], int(product_id))
    current_qty = cart_item["quantity"] if cart_item else 0
    if current_qty + 1 > stock.get("product_quantity", 0):  # 加入後會超過庫存上限
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
    for row in rows:                    # 逐筆處理購物車商品，計算每項小計並組裝模板所需格式
        item_total = row['price'] * row['quantity']
        subtotal  += item_total
        items.append({
            'id'        : row['id'],
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'remove_url': url_for('C.cart_remove', item_id=row['id']),
            'stock'     : row['stock'],
            'is_active' : row['is_active'],
        })

    shipping = 60 if subtotal > 0 else 0    # 有商品才收運費，空購物車不收
    discount = 0
    total    = subtotal + shipping - discount

    summary = {
        'subtotal': subtotal,
        'shipping': shipping,
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


# ── 結帳 ──────────────────────────────────────────────────────────────────────────────────────
# 對應路由：GET + POST /checkout
@requestParsor
def checkout_service(name="",phone="",address="",payment="",shipping="",note="",card_id="",card_number=""):
    user_account = session.get(SESSION_AUTHO)
    rows = get_cart_items(user_account)

    if not rows:                        # 購物車是空的，不允許進入結帳
        flash("購物車是空的","error")
        return redirect(url_for("C.cart"))

    if request.method == "GET":         # 顯示結帳表單
        user = getUser(
            {"user_account": user_account},
            "user_name", "user_mobile", "user_address"
        )

        order_items = []
        subtotal    = 0
        for row in rows:                # 逐筆計算每項金額，組裝結帳頁的商品列表
            item_total  = row['price'] * row['quantity']
            subtotal   += item_total
            order_items.append({
                "name" : row['name'],
                "qty"  : row['quantity'],
                "price": item_total,
            })

        shipping = 60
        total    = subtotal + shipping

        saved_cards = get_member_cards(user_account)

        return render_template("checkout.html",
            submit_url=url_for("C.checkout"),
            order_items=order_items,
            summary={"shipping": shipping, "total": total},
            payment_methods=["ATM 轉帳", "信用卡", "貨到付款"],
            shipping_methods=["宅配到府", "超商取貨"],
            form={
                "name"   : user.get("user_name"),
                "phone"  : user.get("user_mobile"),
                "address": user.get("user_address")
            },
            saved_cards=saved_cards,
            auth=get_auth(user_account)
        )

    # ── POST：驗證表單並建立訂單 ──
    if not name:
        flash("請填寫收件人姓名", "error")
        return redirect(url_for("C.checkout"))
    if not address:
        flash("請填寫收件地址", "error")
        return redirect(url_for("C.checkout"))
    if not payment:
        flash("請選擇付款方式", "error")
        return redirect(url_for("C.checkout"))
    if not shipping:
        flash("請選擇配送方式", "error")
        return redirect(url_for("C.checkout"))
    if phone and not validateMobile(phone):
        flash("手機格式錯誤，請輸入09開頭的10位數字", "error")
        return redirect(url_for("C.checkout"))

    credit_card_number = None
    if payment == "信用卡":
        if card_id:
            saved_cards = get_member_cards(user_account)
            matched = next((c for c in saved_cards if str(c["id"]) == card_id), None)
            if not matched:
                flash("所選信用卡不存在", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = matched["card_number"][-4:]
        else:
            if not card_number:
                flash("請輸入信用卡卡號", "error")
                return redirect(url_for("C.checkout"))
            if not validateCreditCard(card_number):
                flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = card_number.replace(" ", "")[-4:]

    for row in rows:                    # 結帳前重新確認商品狀態與庫存
        product = get_product_by_id(row["product_id"])
        if not product or not product.get("is_active"):
            flash(f"「{row['name']}」已下架，請回購物車移除後再結帳", "error")
            return redirect(url_for("C.cart"))
        stock     = get_product_stock(row["product_id"])
        available = stock.get("product_quantity", 0) if stock else 0
        if row["quantity"] > available:
            flash(f"「{row['name']}」庫存不足（剩餘 {available} 件），請回購物車調整數量", "error")
            return redirect(url_for("C.cart"))

    total    = sum(row['price'] * row['quantity'] for row in rows) + 60     # 重新計算總額防止前端竄改
    order_id = insert_order(user_account, total, payment, shipping, address, note, credit_card_number)

    # 逐筆將購物車商品寫入訂單明細、扣庫存、產生序號、發放道具或傳送序號
    for row in rows:
        # 建立訂單明細並取得 id
        order_item_id = insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])
        # 扣減庫存
        deduct_product_stock(row["product_id"], row['quantity'])
        # 產生唯一序號並存入訂單明細，防止重複兌換
        serial = getVerifyToken(16)
        update_order_item_serial(order_item_id, serial)
        # 查出商品的 MC 道具 ID
        product = get_product_by_id(row["product_id"])
        mc_item_id = product.get("mc_item_id")
        if mc_item_id:
            # 寶石類：直接發道具進背包
            give_item(user_account, mc_item_id, row["quantity"])
        else:
            # 序號類：透過 RCON 傳序號給玩家
            notify_player(user_account, f"你的兌換序號：{serial}")

    # 清空購物車
    clear_cart(user_account)
    # 訂單建立成功通知
    notify_player(user_account, f"🎉 訂單 #{order_id} 建立成功！感謝購買！")
    flash("訂單建立成功！", "success")
    return redirect(url_for("D.member"))

# ── 取消訂單 ──────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /order/<order_id>/cancel
def order_cancel_service(order_id):
    user_account = session[SESSION_AUTHO]

    order = get_order(order_id, user_account)
    if not order:                       # 訂單不存在、不屬於本人，或狀態不是「處理中」
        flash("訂單不存在")
        return redirect(url_for("D.member"))

    order_items = get_order_items(order_id)
    cancel_order(order_id)
    for item in order_items:            # 取消後補回各商品庫存
        restore_product_stock(item["product_id"], item["quantity"])
    flash("訂單已取消", "success")
    return redirect(url_for("D.member"))

# ── 序號兌換 ──────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /redeem
# 玩家輸入序號後，驗證是否有效且未兌換，成功則標記已兌換並透過 RCON 通知玩家
@requestParsor
def redeem_service(serial_code=""):
    user_account = session[SESSION_AUTHO]
    
    if not serial_code:
        flash("請輸入序號", "error")
        return redirect(url_for("B.index"))
    
    # 查詢序號是否有效且未兌換
    item = get_order_item_by_serial(serial_code)
    if not item:
        flash("序號無效或已使用", "error")
        return redirect(url_for("B.index"))
    
    # 標記為已兌換，防止重複使用
    redeem_serial(serial_code)
    # 透過 RCON 通知玩家兌換成功
    notify_player(user_account, f"✅ 序號兌換成功！道具已發放！")
    flash("兌換成功！", "success")
    return redirect(url_for("B.index"))