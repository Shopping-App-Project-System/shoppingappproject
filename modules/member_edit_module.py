# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product_by_id,get_product_stock,get_product_pics
from AuthDecorator import loginRequired
from settings import SESSION_AUTHO,PROFILE_PIC_FOLDER
from models_shopping import search_orders,get_orders,getUser,updateUser
from utils import get_auth,validatePhone,save_image,del_imgae
# _______________________________________初始化___________________________________________
bp = Blueprint("member_edit",__name__)

# ________________________________________API_____________________________________________
@bp.route("/member/edit", methods=["GET", "POST"])
@loginRequired
def member_edit():
    user_account = session.get(SESSION_AUTHO)

    if request.method == "GET":
        user = getUser(
            {"user_account": user_account},
            "user_name", "user_email", "user_mobile", "user_account"
        )
        user["level"] = "一般會員"
        return render_template("member_edit.html",
            user=user,
            auth=get_auth(user_account)
        )

    name   = request.form.get("name")
    mobile = request.form.get("mobile")
    file   = request.files.get("profile_pic")

    if mobile and not validatePhone(mobile):
        flash("手機格式錯誤", "error")
        return redirect(url_for("member_edit"))

    update_data = {"user_name": name, "user_mobile": mobile}
   
    
    if file and file.filename != "":
        old_pic_path = getUser({"user_account":user_account}, "pic_path")
        new_pic_path = save_image(file, PROFILE_PIC_FOLDER, filename=user_account)
        update_data["pic_path"] = new_pic_path
        del_imgae(old_pic_path)
    
    updateUser(update_data, {"user_account": user_account})
    flash("資料更新成功", "success")
    return redirect(url_for("member"))