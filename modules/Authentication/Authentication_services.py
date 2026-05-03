# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash
from flask_mail import Message
from mariadb import IntegrityError

# _______________________________________自定義模組_______________________________________
from models import updateUser,createUser,getUser
from settings import SESSION_AUTHO,MAIL_USERNAME,PROFILE_PIC_PATH,APP_PORT,PROFILE_TEMP_PATH,PROFILE_TEMP_FOLDER
from utils import checkUserInput,getResponseForm,getVerifyToken,getRandomVerifyCode,move_image,validateMobile,validateEmail,getResponseFile,copy_image,save_image
from extension import mail
# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________

def forgot_account_service():
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

    mail_msg = Message("取得帳號驗證信", sender=MAIL_USERNAME, recipients=[res_email])
    
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")

def forgot_password_service():
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

    mail_msg = Message("重設密碼驗證信", sender=MAIL_USERNAME, recipients=[res_email])
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/password/email/{token}/verify/code">點擊此連結，即可重設密碼</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")

def forgot_verify_account_service(token):
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

def reset_verify_password_service(token):
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

def login_service():
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
    return redirect(url_for("B.index"))

def logout_service():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("B.index"))

def register_service():
    if request.method == "GET":
        return render_template("register.html")
    
    msg = checkUserInput(request.form, name="姓名",account="帳號",password="密碼",mobile="手機",email="信箱",address="地址")
    
    if msg:
        flash("請輸入"+msg)
        return render_template("register.html")
    
    res_name, res_account, res_password, res_mobile, res_email, res_address = getResponseForm(request.form)
    
    # 測試用，信箱添加格式驗證（正規表示式）
    if not validateEmail(res_email):
        flash("信箱格式錯誤")
        return render_template("register.html")

    # 測試用，手機添加格式驗證（正規表示式）
    if not validateMobile(res_mobile):
        flash("手機格式錯誤")
        return render_template("register.html")
    
    try:
        createUser(res_name, res_account, res_password, res_mobile, res_email, res_address)
    except IntegrityError:
        flash("帳號已存在")
        return render_template("register.html")
    
    file = getResponseFile(request.files, "profile_pic")
    if file is None or file.filename == "":
        user_filename = res_account + ".png"
        ori_pic_path = PROFILE_TEMP_PATH.format("default.png")
        user_pic_path = PROFILE_TEMP_PATH.format(user_filename)
        user_pic_path = copy_image(ori_pic_path, user_pic_path)
    else: 
        user_pic_path = save_image(file, PROFILE_TEMP_FOLDER, filename=res_name)   
        
    updateUser({"pic_path":user_pic_path}, {"user_account":res_account})
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_account":res_account})
    
    mail_msg = Message("註冊驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/register/email/{token}/verify/code">驗證信</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    return render_template("login.html")


def reset_password_service(token):
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

def verify_register_service(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    res_code = getResponseForm(request.form, "code")
    user = getUser({"token":token},"user_account","code","pic_path")
    user_account,user_code,user_pic_path = user["user_account"],user["code"],user["pic_path"]

    if res_code != user_code:
        flash("驗證失敗")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    # 驗證成功：將大頭照從暫存移至正式路徑，並啟用帳號
    user_filename = f"{user_account}.{user_pic_path.rsplit('.',1)[-1]}"
    new_pic_path = PROFILE_PIC_PATH.format(user_filename)
    new_pic_path = move_image(user_pic_path, new_pic_path)
    
    updateUser({"verify_status":True,"pic_path":new_pic_path},{"token":token})
    
    flash("驗證成功")
    return render_template("login.html")