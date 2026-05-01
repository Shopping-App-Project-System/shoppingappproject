# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly
from utils import checkUserInput,getResponseForm
from models_shopping import getUser
from settings import SESSION_AUTHO

# _______________________________________初始化___________________________________________
bp = Blueprint("login",__name__)

# ________________________________________API_____________________________________________

@bp.route("/login",methods = ["POST","GET"])
@guestOnly
def login():
    if request.method == "GET":
        return render_template("login.html")

    msg = checkUserInput(request.form, account="帳號", password="密碼", email="信箱")
    if msg :
        flash("請輸入"+msg)
        return render_template("login.html")
    
    res_account,res_password,res_email = getResponseForm(request.form,"account","password","email")
    user = getUser({"user_account":res_account},"user_account","user_password","user_email","verify_status")
    if user is None:
        flash("查無此帳號")
        return render_template("login.html")
    
    user_account = user["user_account"]
    user_password = user["user_password"]
    user_email = user["user_email"]
    verify_status = user["verify_status"]
    
    if res_password != user_password or res_email != user_email:
        flash("密碼或信箱輸入錯誤")
        return render_template("login.html")
    
    if not verify_status:
        flash("此帳號尚未通過驗證，請透過信箱中的驗證信，進行驗證")
        return render_template("login.html")
    
    session[SESSION_AUTHO] = user_account
    flash(f"welcome {user_account} !")
    return redirect(url_for("index"))