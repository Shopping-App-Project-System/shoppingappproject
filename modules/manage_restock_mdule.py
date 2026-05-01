# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product_by_id,set_product_active,add_log
from AuthDecorator import adminRequired
from settings import SESSION_AUTHO

# _______________________________________初始化___________________________________________
bp = Blueprint("manage_restock",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/restock", methods=["POST"])
@adminRequired
def manage_restock():
    product_id = request.form.get("product_id")
    product    = get_product_by_id(product_id)
    set_product_active(product_id, 1)
    add_log(session.get(SESSION_AUTHO), "重新上架", product_id, product["name"])
    flash("商品已重新上架", "success")
    return redirect(url_for("manage"))
