# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_cart_items,getUser,insert_order,insert_order_item,clear_cart
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
from utils import get_auth,validatePhone,validateCreditCard
# _______________________________________初始化___________________________________________
bp = Blueprint("checkout",__name__)

# ________________________________________API_____________________________________________
@bp.route("/checkout", methods=["GET", "POST"])
@loginRequired
def checkout():
    user_account = session.get(SESSION_AUTHO)
    rows = get_cart_items(user_account)

    if not rows:
        flash("購物車是空的")
        return redirect(url_for("cart"))

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
            submit_url=url_for("checkout"),
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

    if phone and not validatePhone(phone):
        flash("手機格式錯誤，請輸入09開頭的10位數字", "error")
        return redirect(url_for("checkout"))

    if payment_method == "信用卡":
        if not card_number:
            flash("請輸入信用卡卡號", "error")
            return redirect(url_for("checkout"))
        if not validateCreditCard(card_number):
            flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
            return redirect(url_for("checkout"))

    total    = sum(row['price'] * row['quantity'] for row in rows) + 60
    order_id = insert_order(user_account, total, payment_method, delivery_method, address, note)
    for row in rows:
        insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])
    
    clear_cart(user_account)
    flash(f"訂單 #{order_id} 建立成功！", "success")
    return redirect(url_for("member"))