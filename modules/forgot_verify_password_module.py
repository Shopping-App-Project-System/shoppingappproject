# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly,tokenRequired
from utils import checkUserInput,getResponseForm
from models_shopping import getUser

# _______________________________________初始化___________________________________________
bp = Blueprint("forgot_verify_password",__name__)

# ________________________________________API_____________________________________________
# 重設密碼驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後顯示重設密碼頁
@bp.route("/login/find/password/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def reset_verify_password(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    
    res_code = getResponseForm(request.form, "code")
    user_code = getUser({"token":token},"code")
    if res_code == user_code:
        flash("驗證成功")
        return render_template("reset_password.html",token=token)
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    