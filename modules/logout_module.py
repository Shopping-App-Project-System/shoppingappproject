# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO

# _______________________________________初始化___________________________________________
bp = Blueprint("logout",__name__)

# ________________________________________API_____________________________________________

# 登出：清除 session 中的登入資訊並導回首頁
@bp.route("/logout")
@loginRequired
def logout():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("index"))