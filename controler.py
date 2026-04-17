# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash
from flask_mail import Mail, Message
from shutil import copy,move

# _______________________________________自定義模組_______________________________________
import settings
from models import Models
from AuthDecorator import guestOnly,tokenRequired,loginRequired
from utils import getRandomVerifyCode,getResponseForm,getResponseFile,getVerifyToken,checkUserInput


# _______________________________________初始化___________________________________________
app = Flask(__name__)
app.secret_key = settings.SESSION_KEY

model = Models()

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cbes502034@gmail.com'
app.config['MAIL_PASSWORD'] = "wqsemkvtjlzakidy"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



# ________________________________________API_____________________________________________

@app.route("/")
def index():
    if session.get(settings.SESSION_AUTHO):
        return render_template("index.html",
                               auth={"logged_in":True,
                                     "account":session.get(settings.SESSION_AUTHO),
                                     "profile_pic":model.getUser({"user_account":session.get(settings.SESSION_AUTHO)}, "pic_path")
                                     })
    return render_template("index.html")

@app.route("/register",methods = ["POST","GET"])
@guestOnly
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    msg = checkUserInput(request.form, name="姓名",account="帳號",password="密碼",mobile="手機",email="信箱",address="地址")
    
    if msg:
        flash("請輸入"+msg)
        return render_template("register.html")
    
    res_name, res_account, res_password, res_mobile, res_email, res_address = getResponseForm(request.form)
    model.createUser(res_name, res_account, res_password, res_mobile, res_email, res_address)
    
    file = getResponseFile(request.files, "profile_pic")
    if file is None or file.filename == "":
        user_filename = res_account+".png"
        
        ori_pic_path = settings.PROFILE_TEMP_PATH.format("default.png")
        user_pic_path = settings.PROFILE_TEMP_PATH.format(user_filename)
        
        copy(ori_pic_path,user_pic_path)
    else:
        user_filename = f"{res_name}.{file.filename.rsplit('.',1)[-1]}"
        user_pic_path = settings.PROFILE_TEMP_PATH.format(user_filename)
        file.save(user_pic_path)
        
    model.updateUser({"pic_path":user_pic_path}, {"user_account":res_account})
    token = getVerifyToken(32)
    model.updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    model.updateUser({"code":code},{"user_account":res_account})
    
    msg = Message("註冊驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/register/email/{token}/verify/code">驗證信</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    return render_template("login.html")
    

@app.route("/register/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(model,refresh = True)
def registerEmailVerifyCode(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    res_code = getResponseForm(request.form, "code")
    user_account,user_code,user_pic_path = model.getUser({"token":token},"user_account","code","pic_path")

    if res_code != user_code:
        flash("驗證失敗")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    user_filename = f"{user_account}.{user_pic_path.rsplit('.',1)[-1]}"
    new_pic_path = settings.PROFILE_PIC_PATH.format(user_filename)
    move(user_pic_path,new_pic_path)
    
    model.updateUser({"verify_status":True,"pic_path":new_pic_path},{"token":token})
    
    flash("驗證成功")
    return render_template("login.html")
    
@app.route("/login",methods = ["POST","GET"])
@guestOnly
def login():
    if request.method == "GET":
        return render_template("login.html")

    msg = checkUserInput(request.form, account="帳號", password="密碼", email="信箱")
    if msg :
        flash("請輸入"+msg)
        return render_template("login.html")
    
    res_account,res_password,res_email = getResponseForm(request.form,"account","password","email")
    user = model.getUser({"user_account":res_account},"user_name","user_account","user_password","user_email","verify_status")
    if user is None:
        flash("查無此帳號")
        return render_template("login.html")
    
    user_name = user[0]
    user_account = user[1]
    user_password = user[2]
    user_email = user[3]
    user_verify_status = user[4]
    
    if res_password != user_password or res_email != user_email:
        flash("密碼或信箱輸入錯誤")
        return render_template("login.html")
    
    if not user_verify_status:
        flash("此帳號尚未通過驗證，請透過信箱中的驗證信，進行驗證")
        return render_template("login.html")
    
    session[settings.SESSION_AUTHO] = user_account
    flash(f"welcome {user_name} !")
    return redirect(url_for("index"))


@app.route("/login/find/password",methods = ["POST","GET"])
@guestOnly
def loginFindPassword():
    if request.method == "GET":
        return render_template("find_password.html")

    msg = checkUserInput(request.form,account="帳號",email="信箱")
    if msg:
        flash("請輸入"+msg)
        return render_template("find_password.html")
    res_account,res_email = getResponseForm(request.form, "account","email")
    user_email = model.getUser({"user_account":res_account},"user_email")
    
    if user_email is None:
        flash("查無此帳號")
        return render_template("find_password.html")
    
    if res_email != user_email:
        flash("信箱輸入錯誤")
        return render_template("find_password.html")
    
    token = getVerifyToken(32)
    model.updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    model.updateUser({"code":code},{"user_account":res_account})
    
    msg = Message("重設密碼驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/login/find/password/email/{token}/verify/code">點擊此連結，即可重設密碼</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")


@app.route("/login/find/password/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(model,refresh = True)
def loginFindPasswordVerifyCode(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    
    res_code = getResponseForm(request.form, "code")
    user_code = model.getUser({"token":token},"code")
    if res_code == user_code:
        flash("驗證成功")
        return render_template("reset_password.html",token=token)
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    

@app.route("/login/reset/password/<token>",methods=["POST","GET"])
@guestOnly
@tokenRequired(model,refresh = True)
def loginResetPassword(token):
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
    
    user_password = model.getUser({"token":token},"user_password")
    if res_password == user_password:
        flash("不可使用重複的密碼，請更新")
        return render_template("reset_password.html", token=token)
    model.updateUser({"user_password":res_password},{"token":token})
    flash("密碼更新成功")
    return render_template("login.html")

    
@app.route("/login/find/account",methods = ["POST","GET"])
@guestOnly
def loginFindAccount():
    if request.method == "GET":
        return render_template("find_account.html")

    msg = checkUserInput(request.form,email="信箱")
    if msg:
        flash("請輸入"+msg)
        return render_template("find_account.html")
    res_email = getResponseForm(request.form, "email")
    user_account = model.getUser({"user_email":res_email},"user_email")
    
    if user_account is None:
        flash("信箱輸入錯誤")
        return render_template("find_account.html")
    
    token = getVerifyToken(32)
    model.updateUser({"token":token},{"user_email":res_email})

    code = getRandomVerifyCode(6)
    model.updateUser({"code":code},{"user_email":res_email})

    
    msg = Message("取得帳號驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")


@app.route("/login/find/account/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(model,refresh = True)
def loginFindAccountVerifyCode(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")


    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    res_code = getResponseForm(request.form, "code")
    user_code,user_account = model.getUser({"token":token},"code","user_account")
    if res_code == user_code:
        flash(f"您的帳號為{user_account}")
        return render_template("login.html")
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

@app.route("/logout")
@loginRequired
def logout():
    session.pop(settings.SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("index"))

@app.route("/member")
@loginRequired
def member():
    flash("請先登入")
    return render_template("member.html")

@app.route("/cart")
@loginRequired
def cart():
    flash("請先登入")
    return render_template("cart.html")
    
    
if __name__ == "__main__":
    """先於settings.py中設定APP_PORT"""
    app.run(debug=True,use_reloader=False,port=settings.APP_PORT)
