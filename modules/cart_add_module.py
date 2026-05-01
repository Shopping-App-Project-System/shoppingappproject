# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product,upsert_cart
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
# _______________________________________初始化___________________________________________
bp = Blueprint("cart_add",__name__)

# ________________________________________API_____________________________________________
@bp.route("/cart/add", methods=["POST", "GET"])
@loginRequired
def cart_add():
    if request.method == "GET":
        return redirect(url_for("cart"))

    next_url = request.form.get("next") or url_for("cart")
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
