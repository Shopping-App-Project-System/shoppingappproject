# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_order,cancel_order
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO
# _______________________________________初始化___________________________________________
bp = Blueprint("order_cancel",__name__)

# ________________________________________API_____________________________________________
@bp.route("/order/<int:order_id>/cancel", methods=["GET","POST"])
@loginRequired
def order_cancel(order_id):
    if request.method == "GET":
        return redirect(url_for("index"))
    user_account = session[SESSION_AUTHO]
    
    order = get_order(order_id, user_account)
    if not order:
        flash("訂單不存在")
        return redirect(url_for("member"))
    
    cancel_order(order_id)
    flash("訂單已取消", "success")
    return redirect(url_for("member"))
