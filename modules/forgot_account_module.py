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
bp = Blueprint("forgot_account",__name__)

# ________________________________________API_____________________________________________
   
# 找回帳號：GET 顯示表單，POST 以信箱查詢帳號並發送驗證信
@bp.route("/login/find/account",methods = ["POST","GET"])
@guestOnly
def forgot_account():
    if request.method == "GET":
        return render_template("find_account.html")

    msg = checkUserInput(request.form,email="信箱")
    if msg:
        flash("請輸入"+msg)
        return render_template("find_account.html")
    res_email = getResponseForm(request.form, "email")
    user_account = getUser({"user_email":res_email},"user_email")
    
    if user_account is None:
        flash("信箱輸入錯誤")
        return render_template("find_account.html")
    
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_email":res_email})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_email":res_email})

    # msg = Message("取得帳號驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    
    # 測試用，發送取得帳號驗證信
    msg = Message("取得帳號驗證信", sender=MAIL_USERNAME, recipients=[res_email])
    
    msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")
