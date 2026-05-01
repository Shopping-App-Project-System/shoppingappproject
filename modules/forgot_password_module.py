# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint
from flask_mail import Message

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly
from utils import checkUserInput,getResponseForm,getVerifyToken,getRandomVerifyCode
from models_shopping import getUser,updateUser
from settings import MAIL_USERNAME,APP_PORT
from extension import mail

# _______________________________________初始化___________________________________________
bp = Blueprint("forgot_password",__name__)

# ________________________________________API_____________________________________________

# 忘記密碼：GET 顯示表單，POST 驗證帳號與信箱後發送重設密碼驗證信
@bp.route("/login/find/password",methods = ["POST","GET"])
@guestOnly
def forgot_password():
    if request.method == "GET":
        return render_template("find_password.html")

    msg = checkUserInput(request.form,account="帳號",email="信箱")
    if msg:
        flash("請輸入"+msg)
        return render_template("find_password.html")
    res_account,res_email = getResponseForm(request.form, "account","email")
    user_email = getUser({"user_account":res_account},"user_email")
    
    if user_email is None:
        flash("查無此帳號")
        return render_template("find_password.html")
    
    if res_email != user_email:
        flash("信箱輸入錯誤")
        return render_template("find_password.html")
    
    # 產生新 token 與驗證碼，發送重設密碼驗證信
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_account":res_account})
    
    # msg = Message("重設密碼驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    
    # 測試用，發送重設密碼驗證信
    msg = Message("重設密碼驗證信", sender=MAIL_USERNAME, recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/password/email/{token}/verify/code">點擊此連結，即可重設密碼</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")