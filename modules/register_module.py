# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint
from flask_mail import Message
from mariadb import IntegrityError

# _______________________________________自定義模組_______________________________________
import models_shopping
import settings
from AuthDecorator import guestOnly
from extension import mail
from utils import checkUserInput,getResponseForm,validateEmail,validatePhone,getResponseFile,copy_image,save_image,getVerifyToken,getRandomVerifyCode

# _______________________________________初始化___________________________________________
bp = Blueprint("register",__name__)

# ________________________________________API_____________________________________________ 
# 註冊：GET 顯示表單，POST 驗證輸入、建立帳號、複製預設大頭貼、發送驗證信
@bp.route("/register",methods = ["POST","GET"])
@guestOnly
def register():
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
    if not validatePhone(res_mobile):
        flash("手機格式錯誤")
        return render_template("register.html")
    
    try:
        models_shopping.createUser(res_name, res_account, res_password, res_mobile, res_email, res_address)
    except IntegrityError:
        flash("帳號已存在")
        return render_template("register.html")
    
    file = getResponseFile(request.files, "profile_pic")
    if file is None or file.filename == "":
        user_filename = res_account + ".png"
        ori_pic_path = settings.PROFILE_TEMP_PATH.format("default.png")
        user_pic_path = settings.PROFILE_TEMP_PATH.format(user_filename)
        user_pic_path = copy_image(ori_pic_path, user_pic_path)
    else: 
        user_pic_path = save_image(file, settings.PROFILE_TEMP_FOLDER, filename=res_name)   
        
    models_shopping.updateUser({"pic_path":user_pic_path}, {"user_account":res_account})
    token = getVerifyToken(32)
    models_shopping.updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    models_shopping.updateUser({"code":code},{"user_account":res_account})
    
    msg = Message("註冊驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/register/email/{token}/verify/code">驗證信</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    return render_template("login.html")