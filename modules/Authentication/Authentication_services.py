# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash
from flask_mail import Message
from datetime import datetime, timedelta

# _______________________________________自定義模組_______________________________________
from models import updateUser,createUser,getUser,getUserList,updateSessionToken,clearSessionToken
from settings import SESSION_AUTHO,MAIL_USERNAME,CODE_EXPIRE_MINUTES,PROFILE_FOLDER,PROFILE_DEFAULT_PATH,SESSION_EXPIRE_HOURS
from utils import checkUserInput,getVerifyToken,getRandomVerifyCode,validateEmail,requestParsor,validateMCUserAccount,_is_expired,_mc_mail_html
from extension import mail
from cloudinary_helper import save_image
# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________

@requestParsor
def forgot_account_service(email):
    if request.method == "GET":
        return render_template("find_account.html")

    msg = checkUserInput(("信箱",email))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("find_account.html")

    user = getUser({"user_email":email},"user_account","user_email")
    if user is None:
        flash("信箱輸入錯誤","error")
        return render_template("find_account.html")

    token = getVerifyToken(32)
    code = getRandomVerifyCode(6)
    expires_at = datetime.now() + timedelta(minutes=CODE_EXPIRE_MINUTES)
    updateUser({"token":token,"code":code,"code_expires_at":expires_at},{"user_email":email})

    mail_msg = Message("取得帳號驗證信", sender=MAIL_USERNAME, recipients=[email])
    mail_msg.html = _mc_mail_html(
        account=user["user_account"],
        code=code,
        token=token,
        route=f"/login/find/account/email/{token}/verify/code",
        title="找回帳號",
        subtitle="請完成驗證以取得你的帳號"
    )
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序","success")
    return render_template("login.html")


@requestParsor
def forgot_password_service(account,email):
    if request.method == "GET":
        return render_template("find_password.html")

    msg = checkUserInput(("帳號",account),("信箱",email))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("find_password.html")

    user_email = getUser({"user_account":account},"user_email")
    if user_email is None:
        flash("查無此帳號","error")
        return render_template("find_password.html")

    if email != user_email:
        flash("信箱輸入錯誤","error")
        return render_template("find_password.html")

    token = getVerifyToken(32)
    code = getRandomVerifyCode(6)
    expires_at = datetime.now() + timedelta(minutes=CODE_EXPIRE_MINUTES)
    updateUser({"token":token,"code":code,"code_expires_at":expires_at},{"user_account":account})

    mail_msg = Message("重設密碼驗證信", sender=MAIL_USERNAME, recipients=[email])
    mail_msg.html = _mc_mail_html(
        account=account,
        code=code,
        token=token,
        route=f"/login/find/password/email/{token}/verify/code",
        title="重設密碼",
        subtitle="請完成驗證以重設你的密碼"
    )
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序","success")
    return render_template("login.html")


@requestParsor
def forgot_verify_account_service(token,code):
    if request.method == "GET":
        expires_at = getUser({"token":token},"code_expires_at")
        if expires_at is None or _is_expired(expires_at):
            flash("驗證碼已過期，請重新操作","error")
            return render_template("login.html")
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    user = getUser({"token":token},"code","user_account","code_expires_at")
    if _is_expired(user["code_expires_at"]):
        flash("驗證碼已過期，請重新操作","error")
        return render_template("login.html")

    if code == user["code"]:
        flash(f"您的帳號為 {user['user_account']}","success")
        return render_template("login.html")

    flash("驗證失敗","error")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")


@requestParsor
def reset_verify_password_service(token,code):
    if request.method == "GET":
        expires_at = getUser({"token":token},"code_expires_at")
        if expires_at is None or _is_expired(expires_at):
            flash("驗證碼已過期，請重新操作","error")
            return render_template("login.html")
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    user = getUser({"token":token},"code","code_expires_at")
    if _is_expired(user["code_expires_at"]):
        flash("驗證碼已過期，請重新操作","error")
        return render_template("login.html")

    if code == user["code"]:
        flash("驗證成功","success")
        return render_template("reset_password.html",token=token)

    flash("驗證失敗","error")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")


@requestParsor
def login_service(account,password,email,force):
    if request.method == "GET":
        return render_template("login.html")
    force = str(force) == "1"
    msg = checkUserInput(("帳號",account),("密碼",password),("信箱",email))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("login.html")

    user = getUser({"user_account":account},"user_account","user_password","user_email","verify_status")
    if user is None:
        flash("查無此帳號","error")
        return render_template("login.html")

    if password != user["user_password"] or email != user["user_email"]:
        flash("密碼或信箱輸入錯誤","error")
        return render_template("login.html")

    if not user["verify_status"]:
        flash("此帳號尚未通過驗證，請透過信箱中的驗證信，進行驗證","error")
        return render_template("login.html")
    user_session = getUser({"user_account": account}, "session_token")
    if user_session:
        if not force:
            flash("此帳號已在其他裝置登入，請確認後強制登入", "error")
            return render_template("login.html", show_force=True, account=account, password=password, email=email)
    
    token = getVerifyToken(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)
    updateSessionToken(token, expires_at, account)
        
    session[SESSION_AUTHO] = user["user_account"]
    session["session_token"] = token
    if user["user_account"] == "admin":
        return redirect(url_for("D.manage"))
    flash(f"welcome {user['user_account']} !","success")
    return redirect(url_for("B.index"))


def logout_service():
    account = session.get(SESSION_AUTHO)
    if account:
        clearSessionToken(account)
    session.pop(SESSION_AUTHO, None)
    session.pop("session_token", None)
    flash("已登出", "success")
    return redirect(url_for("B.index"))


@requestParsor
def register_service(account,password,email,profile_pic):
    if request.method == "GET":
        return render_template("register.html")

    msg = checkUserInput(("帳號",account),("密碼",password),("信箱",email))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("register.html")

    if not validateEmail(email):
        flash("信箱格式錯誤","error")
        return render_template("register.html")

    if not validateMCUserAccount(account):
        flash("帳號格式錯誤","error")
        return render_template("register.html")

    # 帳號與信箱唯一判斷
    user_list = getUserList("user_account","user_email")
    if any(u["user_account"] == account for u in user_list):
        flash("帳號已被使用","error")
        return render_template("register.html")
    if any(u["user_email"] == email for u in user_list):
        flash("信箱已被使用","error")
        return render_template("register.html")

    # 寫入資料庫（保留 Exception 作為最後防線）
    try:
        createUser(account,password,email)
    except Exception:
        flash("註冊失敗，請稍後再試","error")
        return render_template("register.html")

    if profile_pic and profile_pic.filename != "":
        pic_url = save_image(profile_pic, PROFILE_FOLDER, filename=account)
    else:
        pic_url = PROFILE_DEFAULT_PATH

    token = getVerifyToken(32)
    code = getRandomVerifyCode(6)
    expires_at = datetime.now() + timedelta(minutes=CODE_EXPIRE_MINUTES)

    updateUser({
        "pic_path": pic_url,
        "token": token,
        "code": code,
        "code_expires_at": expires_at
    }, {"user_account": account})

    mail_msg = Message("註冊驗證信", sender=MAIL_USERNAME, recipients=[email])
    mail_msg.html = _mc_mail_html(
        account=account,
        code=code,
        token=token,
        route=f"/register/email/{token}/verify/code",
        title="帳號驗證",
        subtitle="請完成驗證以加入伺服器"
    )
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序","success")
    return render_template("login.html")


@requestParsor
def reset_password_service(token,password,confirm_password):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/reset/password/{token}")

    msg = checkUserInput(("密碼",password),("確認密碼",confirm_password))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("reset_password.html",token=token)

    if password != confirm_password:
        flash("密碼與確認密碼不同，請重新輸入","error")
        return render_template("reset_password.html",token=token)

    user_password = getUser({"token":token},"user_password")
    if password == user_password:
        flash("不可使用重複的密碼，請更新","error")
        return render_template("reset_password.html",token=token)

    updateUser({"user_password":password},{"token":token})
    flash("密碼更新成功","success")
    return render_template("login.html")


@requestParsor
def verify_register_service(token,code):
    if request.method == "GET":
        expires_at = getUser({"token":token},"code_expires_at")
        if expires_at is None or _is_expired(expires_at):
            flash("驗證碼已過期，請重新註冊","error")
            return render_template("login.html")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg,"error")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    user = getUser({"token":token},"user_account","code","code_expires_at")
    if _is_expired(user["code_expires_at"]):
        flash("驗證碼已過期，請重新註冊","error")
        return render_template("login.html")

    if code != user["code"]:
        flash("驗證失敗","error")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    updateUser({"verify_status":True},{"token":token})
    flash("驗證成功","success")
    return render_template("login.html")
