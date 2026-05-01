# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_cart_items
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
from utils import get_auth
# _______________________________________初始化___________________________________________
bp = Blueprint("cart",__name__)

# ________________________________________API_____________________________________________
@bp.route("/cart")
@loginRequired
def cart():
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
            'remove_url': url_for('cart_remove', item_id=row['id']),
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
                           checkout_url=url_for("checkout"),
                           auth=get_auth(user_account))