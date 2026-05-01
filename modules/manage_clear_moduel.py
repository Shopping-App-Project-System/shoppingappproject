# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product_by_id,soft_delete_product,add_log
from AuthDecorator import adminRequired
from settings import SESSION_AUTHO

# _______________________________________初始化___________________________________________
bp = Blueprint("manage_clear",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/clear", methods=["POST"])
@adminRequired
def manage_clear():
    product_id = request.form.get("product_id")
    product    = get_product_by_id(product_id)
    soft_delete_product(product_id)
    add_log(session.get(SESSION_AUTHO), "刪除", product_id, product["name"])
    flash("商品已刪除", "success")
    return redirect(url_for("manage"))