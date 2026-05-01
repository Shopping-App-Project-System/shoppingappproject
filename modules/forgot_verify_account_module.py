# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly,tokenRequired
from utils import checkUserInput,getResponseForm
from models_shopping import getUser

# _______________________________________初始化___________________________________________
bp = Blueprint("forgot_verify_account",__name__)

# ________________________________________API_____________________________________________

# 找回帳號驗證碼確認：POST 比對驗證碼，成功後以 flash 顯示帳號給使用者
@bp.route("/login/find/account/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def forgot_verify_account(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    res_code = getResponseForm(request.form, "code")
    user = getUser({"token":token},"code","user_account")
    user_code,user_account = user["code"],user["user_account"]
    if res_code == user_code:
        flash(f"您的帳號為{user_account}")
        return render_template("login.html")
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")
