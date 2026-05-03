# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash

# _______________________________________自定義模組_______________________________________
from models import getUser,get_product,upsert_cart,get_cart_items,remove_cart_item,insert_order,insert_order_item,clear_cart,get_order,cancel_order
from settings import SESSION_AUTHO
from utils import get_auth,validateMobile,validateCreditCard

# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________
def cart_add_service():
    if request.method == "GET":
        return redirect(url_for("C.cart"))

    next_url = request.form.get("next") or url_for("C.cart")
    product_id = request.form.get("product_id")

    if not product_id:
        return redirect(next_url)

    product = get_product(int(product_id))
    if not product:
        flash("商品不存在")
        return redirect(next_url)

    upsert_cart(session[SESSION_AUTHO], int(product_id))
    flash(f"「{product['name']}」已加入購物車", "success")
    return redirect(next_url)

def cart_service():
    # 顯示購物車頁面
    # 從 session 取得登入帳號，查詢購物車商品，計算各項金額後傳給模板
    user_account = session[SESSION_AUTHO]
    rows = get_cart_items(user_account)

    items    = []
    subtotal = 0
    for row in rows:
        item_total = row['price'] * row['quantity']
        subtotal  += item_total
        items.append({
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'remove_url': url_for('C.cart_remove', item_id=row['id']),
        })

    shipping = 60 if subtotal > 0 else 0
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

def cart_remove_service(item_id):
    # 從購物車移除指定商品（GET，對應模板中的 remove_url 連結）
    # 比對 user_account 確保只能刪自己的項目
    remove_cart_item(item_id, session[SESSION_AUTHO])
    return redirect(url_for("C.cart"))

def checkout_service():
    user_account = session.get(SESSION_AUTHO)
    rows = get_cart_items(user_account)

    if not rows:
        flash("購物車是空的","error")
        return redirect(url_for("C.cart"))

    if request.method == "GET":
        user = getUser(
            {"user_account": user_account},
            "user_name", "user_mobile", "user_address"
        )

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

        shipping = 60
        total    = subtotal + shipping

        return render_template("checkout.html",
            submit_url=url_for("C.checkout"),
            order_items=order_items,
            summary={"shipping": shipping, "total": total},
            payment_methods=["信用卡", "ATM 轉帳", "貨到付款"],
            shipping_methods=["宅配到府", "超商取貨"],
            form={
                "name"   : user.get("user_name"),
                "phone"  : user.get("user_mobile"),
                "address": user.get("user_address")
            },
            auth=get_auth(user_account)
        )

    name            = request.form.get("name", "")
    phone           = request.form.get("phone", "")
    address         = request.form.get("address", "")
    payment_method  = request.form.get("payment", "")
    delivery_method = request.form.get("shipping", "")
    note            = request.form.get("note", "")
    card_number     = request.form.get("card_number", "")

    if phone and not validateMobile(phone):
        flash("手機格式錯誤，請輸入09開頭的10位數字", "error")
        return redirect(url_for("C.checkout"))

    if payment_method == "信用卡":
        if not card_number:
            flash("請輸入信用卡卡號", "error")
            return redirect(url_for("C.checkout"))
        if not validateCreditCard(card_number):
            flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
            return redirect(url_for("C.checkout"))

    total    = sum(row['price'] * row['quantity'] for row in rows) + 60
    order_id = insert_order(user_account, total, payment_method, delivery_method, address, note)
    for row in rows:
        insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])
    
    clear_cart(user_account)
    flash(f"訂單 #{order_id} 建立成功！", "success")
    return redirect(url_for("D.member"))

def order_cancel_service(order_id):
    if request.method == "GET":
        return redirect(url_for("B.index"))
    user_account = session[SESSION_AUTHO]
    
    order = get_order(order_id, user_account)
    if not order:
        flash("訂單不存在")
        return redirect(url_for("D.member"))
    
    cancel_order(order_id)
    flash("訂單已取消", "success")
    return redirect(url_for("D.member"))