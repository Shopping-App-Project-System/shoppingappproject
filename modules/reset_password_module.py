# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly,tokenRequired
from utils import checkUserInput,getResponseForm
from models_shopping import getUser,updateUser

# _______________________________________初始化___________________________________________
bp = Blueprint("reset_password",__name__)

# ________________________________________API_____________________________________________

# 重設密碼：POST 驗證新舊密碼不同且兩次輸入一致後更新密碼
@bp.route("/login/reset/password/<token>",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def reset_password(token):
    if request.method == "GET":
    
        return render_template("verify_code.html",token=token,form_action=f"/login/reset/password/{token}")

    msg = checkUserInput(request.form, password="密碼",confirm_password="確認密碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("reset_password.html",token=token)
    
    
    res_password,res_confirm_password = getResponseForm(request.form, "password","confirm_password")
    if res_password != res_confirm_password:
        flash("密碼與確認密碼不同，請重新輸入")
        return render_template("reset_password.html", token=token)
    
    user_password = getUser({"token":token},"user_password")
    if res_password == user_password:
        flash("不可使用重複的密碼，請更新")
        return render_template("reset_password.html", token=token)
    
    updateUser({"user_password":res_password},{"token":token})
    flash("密碼更新成功")
    return render_template("login.html")
