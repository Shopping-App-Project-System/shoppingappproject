# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash
from flask_mail import Message
from mariadb import IntegrityError

# _______________________________________自定義模組_______________________________________
from models import updateUser,createUser,getUser
from settings import SESSION_AUTHO,MAIL_USERNAME,PROFILE_PIC_PATH,APP_PORT,PROFILE_TEMP_PATH,PROFILE_TEMP_FOLDER
from utils import checkUserInput,getResponseForm,getVerifyToken,getRandomVerifyCode,move_image,validateMobile,validateEmail,getResponseFile,copy_image,save_image,requestParsor,validateMCUserAccount
from extension import mail
# _______________________________________初始化___________________________________________

# ________________________________________services_____________________________________________

@requestParsor
def forgot_account_service(email):
    if request.method == "GET":
            return render_template("find_account.html")

    msg = checkUserInput(("信箱",email))
    if msg:
        flash("請輸入"+msg)
        return render_template("find_account.html")
    user_account = getUser({"user_email":email},"user_email")
    
    if user_account is None:
        flash("信箱輸入錯誤")
        return render_template("find_account.html")
    
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_email":email})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_email":email})

    mail_msg = Message("取得帳號驗證信", sender=MAIL_USERNAME, recipients=[email])
    
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")

@requestParsor
def forgot_password_service(account,email):
    if request.method == "GET":
        return render_template("find_password.html")

    msg = checkUserInput(("帳號",account),("信箱",email))
    if msg:
        flash("請輸入"+msg)
        return render_template("find_password.html")

    user_email = getUser({"user_account":account},"user_email")
    
    if user_email is None:
        flash("查無此帳號")
        return render_template("find_password.html")
    
    if email != user_email:
        flash("信箱輸入錯誤")
        return render_template("find_password.html")
    
    # 產生新 token 與驗證碼，發送重設密碼驗證信
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_account":account})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_account":account})

    mail_msg = Message("重設密碼驗證信", sender=MAIL_USERNAME, recipients=[email])
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/login/find/password/email/{token}/verify/code">點擊此連結，即可重設密碼</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")

@requestParsor
def forgot_verify_account_service(token,code):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")


    user = getUser({"token":token},"code","user_account")
    user_code,user_account = user["code"],user["user_account"]
    if code == user_code:
        flash(f"您的帳號為{user_account}")
        return render_template("login.html")
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

@requestParsor
def reset_verify_password_service(token,code):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    
    user_code = getUser({"token":token},"code")
    if code == user_code:
        flash("驗證成功")
        return render_template("reset_password.html",token=token)
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

@requestParsor
def login_service(account,password,email):
    if request.method == "GET":
        return render_template("login.html")

    msg = checkUserInput( ("帳號",account), ("密碼",password), ("信箱",email))
    if msg :
        flash("請輸入"+msg)
        return render_template("login.html")
    
    user = getUser({"user_account":account},"user_account","user_password","user_email","verify_status")
    if user is None:
        flash("查無此帳號")
        return render_template("login.html")
    
    user_account = user["user_account"]
    user_password = user["user_password"]
    user_email = user["user_email"]
    verify_status = user["verify_status"]
    
    if password != user_password or email != user_email:
        flash("密碼或信箱輸入錯誤")
        return render_template("login.html")
    
    if not verify_status:
        flash("此帳號尚未通過驗證，請透過信箱中的驗證信，進行驗證")
        return render_template("login.html")
    
    session[SESSION_AUTHO] = user_account
    if user_account == "admin":
        return redirect(url_for("D.manage"))
    flash(f"welcome {user_account} !")
    return redirect(url_for("B.index"))

def logout_service():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("B.index"))

@requestParsor
def register_service(name,account,password,mobile,email,address,minecraft_name,profile_pic):
    if request.method == "GET":
        return render_template("register.html")
    
    msg = checkUserInput(("姓名",name),("帳號",account),("密碼",password),("手機",mobile),("信箱",email),("地址",address),("MC 角色名",minecraft_name))
    
    if msg:
        flash("請輸入"+msg)
        return render_template("register.html")
    
    # 測試用，信箱添加格式驗證（正規表示式）
    if not validateEmail(email):
        flash("信箱格式錯誤")
        return render_template("register.html")

    # 測試用，手機添加格式驗證（正規表示式）
    if not validateMobile(mobile):
        flash("手機格式錯誤")
        return render_template("register.html")
    
    if not validateMCUserAccount(account):
        flash("帳號格式錯誤")
        return render_template("register.html")
    
    # MC 角色名套用同一套格式驗證（英數+底線、3-16字）
    if not validateMCUserAccount(minecraft_name):
        flash("MC 角色名格式錯誤")
        return render_template("register.html")
    
    try:
        createUser(name,account,password,mobile,email,address,minecraft_name)
    except IntegrityError:
        flash("帳號已存在")
        return render_template("register.html")
    
    if profile_pic is None or profile_pic.filename == "":
        user_filename = account + ".png"
        ori_pic_path = PROFILE_TEMP_PATH.format("default.png")
        user_pic_path = PROFILE_TEMP_PATH.format(user_filename)
        user_pic_path = copy_image(ori_pic_path, user_pic_path)
    else: 
        user_pic_path = save_image(profile_pic, PROFILE_TEMP_FOLDER, filename=name)   
        
    updateUser({"pic_path":user_pic_path}, {"user_account":account})
    token = getVerifyToken(32)
    updateUser({"token":token},{"user_account":account})

    code = getRandomVerifyCode(6)
    updateUser({"code":code},{"user_account":account})
    
    mail_msg = Message("註冊驗證信",sender="cbes502034@gmail.com",recipients=[email])
    mail_msg.html = f"""<div><a href="http://127.0.0.1:{APP_PORT}/register/email/{token}/verify/code">驗證信</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(mail_msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    return render_template("login.html")

@requestParsor
def reset_password_service(token,password,confirm_password):
    if request.method == "GET":
    
        return render_template("verify_code.html",token=token,form_action=f"/login/reset/password/{token}")
    msg = checkUserInput(("密碼",password),("確認密碼",confirm_password))

    if msg:
        flash("請輸入"+msg)
        return render_template("reset_password.html",token=token)
    
    if password != confirm_password:
        flash("密碼與確認密碼不同，請重新輸入")
        return render_template("reset_password.html", token=token)
    
    user_password = getUser({"token":token},"user_password")
    if password == user_password:
        flash("不可使用重複的密碼，請更新")
        return render_template("reset_password.html", token=token)
    
    updateUser({"user_password":password},{"token":token})
    flash("密碼更新成功")
    return render_template("login.html")


@requestParsor
def verify_register_service(token,code):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")

    msg = checkUserInput(("驗證碼",code))
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    user = getUser({"token":token},"user_account","code","pic_path")
    user_account,user_code,user_pic_path = user["user_account"],user["code"],user["pic_path"]
    # print(user)
    if code != user_code:
        flash("驗證失敗")
        return render_template("verify_code.html",token=token,form_action=f"/register/email/{token}/verify/code")
    
    # 驗證成功：將大頭照從暫存移至正式路徑，並啟用帳號
    user_filename = f"{user_account}.{user_pic_path.rsplit('.',1)[-1]}"
    new_pic_path = PROFILE_PIC_PATH.format(user_filename)
    new_pic_path = move_image(user_pic_path, new_pic_path)
    
    updateUser({"verify_status":True,"pic_path":new_pic_path},{"token":token})
    
    flash("驗證成功")
    return render_template("login.html")