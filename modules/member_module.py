# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product_by_id,get_product_stock,get_product_pics
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
from models_shopping import search_orders,get_orders,getUser
from utils import get_auth
# _______________________________________初始化___________________________________________
bp = Blueprint("member",__name__)

# ________________________________________API_____________________________________________
# 會員中心
@bp.route("/member")
@loginRequired
def member():
    user_account = session[SESSION_AUTHO]
    keyword = request.args.get("keyword", "").strip()

    if keyword:
        orders = search_orders(user_account, keyword)
    else:
        orders = get_orders(user_account)

    user = getUser(
        {"user_account": user_account},
        "user_name", "user_account", "user_email", "user_mobile"
    )
    user.update({"level": "一般會員"})
    return render_template("member.html",
        orders=orders,
        user=user,
        auth=get_auth(user_account)
    )