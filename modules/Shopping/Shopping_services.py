# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash

# _______________________________________自定義模組_______________________________________
from models import getUser,get_product,get_product_by_id,get_product_stock,upsert_cart,get_cart_items,remove_cart_item,insert_order,insert_order_item,clear_cart,get_order,cancel_order,get_all_orders,get_member_cards
from settings import SESSION_AUTHO
from utils import get_auth,validateMobile,validateCreditCard,requestParsor

# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________

# ── 加入購物車 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/add
def cart_add_service():
    if request.method == "GET":         # 直接用 GET 訪問此路由時，拒絕並導向購物車
        return redirect(url_for("C.cart"))

    next_url = request.form.get("next") or url_for("C.cart")
    product_id = request.form.get("product_id")

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
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'remove_url': url_for('C.cart_remove', item_id=row['id']),
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
def checkout_service(name="",phone="",address="",payment_method="",delivery_method="",note="",card_id="",card_number=""):
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
    if phone and not validateMobile(phone):     # 有填電話但格式不符（非 09 開頭 10 碼）
        flash("手機格式錯誤，請輸入09開頭的10位數字", "error")
        return redirect(url_for("C.checkout"))

    credit_card_number = None
    if payment_method == "信用卡":              # 付款方式選信用卡時才需要驗證卡號
        if card_id:                             # 用戶選擇了已儲存的卡
            saved_cards = get_member_cards(user_account)
            matched = next((c for c in saved_cards if str(c["id"]) == card_id), None)
            if not matched:                     # card_id 不屬於本人，可能是偽造的請求
                flash("所選信用卡不存在", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = matched["card_number"][-4:]    # 取已儲存卡的後四碼
        else:                                   # 用戶手動輸入卡號
            if not card_number:                 # 選了信用卡但沒有填卡號
                flash("請輸入信用卡卡號", "error")
                return redirect(url_for("C.checkout"))
            if not validateCreditCard(card_number):     # 卡號不是 16 碼數字
                flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = card_number.replace(" ", "")[-4:]  # 取手動輸入卡號的後四碼

    total    = sum(row['price'] * row['quantity'] for row in rows) + 60     # 重新計算總額防止前端竄改
    order_id = insert_order(user_account, total, payment_method, delivery_method, address, note, credit_card_number)
    for row in rows:                            # 逐筆將購物車商品寫入訂單明細
        insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])

    clear_cart(user_account)
    flash(f"訂單 #{order_id} 建立成功！", "success")
    return redirect(url_for("D.member"))


# ── 取消訂單 ──────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /order/<order_id>/cancel
def order_cancel_service(order_id):
    if request.method == "GET":         # 防止誤觸，GET 訪問直接導向首頁
        return redirect(url_for("B.index"))
    user_account = session[SESSION_AUTHO]

    order = get_order(order_id, user_account)
    if not order:                       # 訂單不存在、不屬於本人，或狀態不是「處理中」
        flash("訂單不存在")
        return redirect(url_for("D.member"))

    cancel_order(order_id)
    flash("訂單已取消", "success")
    return redirect(url_for("D.member"))