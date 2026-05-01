# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import remove_cart_item
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
# _______________________________________初始化___________________________________________
bp = Blueprint("cart_remove",__name__)

# ________________________________________API_____________________________________________
@bp.route("/cart/remove/<int:item_id>")
@loginRequired
def cart_remove(item_id):
    # 從購物車移除指定商品（GET，對應模板中的 remove_url 連結）
    # 比對 user_account 確保只能刪自己的項目
    remove_cart_item(item_id, session[SESSION_AUTHO])
    return redirect(url_for("cart"))
