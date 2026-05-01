# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_order,cancel_order,get_all_products
from AuthDecorator import adminRequired
# _______________________________________初始化___________________________________________
bp = Blueprint("manage",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage", methods=["GET"])
@adminRequired
def manage():
    products = get_all_products()
    return render_template("manage.html", products=products)