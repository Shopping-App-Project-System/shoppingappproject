# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import guestOnly,tokenRequired
from utils import checkUserInput,getResponseForm,move_image
from models_shopping import getUser,updateUser
from settings import PROFILE_PIC_PATH

# _______________________________________初始化___________________________________________
bp = Blueprint("verify_register",__name__)

# ________________________________________API_____________________________________________
# 信箱驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後將大頭貼移至正式路徑並啟用帳號
@bp.route("/register/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def verify_register(token):
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