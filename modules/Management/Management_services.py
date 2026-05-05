# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash

# _______________________________________自定義模組_______________________________________
from models import getUser,updateUser,add_product,add_log,get_product_by_id,soft_delete_product,get_all_products,set_product_active,search_orders,get_orders,update_product
from settings import SESSION_AUTHO,UPLOAD_FOLDER,PROFILE_PIC_FOLDER
from utils import get_auth,validateMobile,save_image,del_imgae
# _______________________________________初始化___________________________________________

# _______________________________________services___________________________________________
def manage_add_service():
    name           = request.form.get("name")
    original_price = request.form.get("original_price")
    sale_price     = request.form.get("sale_price") or None  # 空字串轉 None，沒填特價就存 NULL
    description    = request.form.get("description")
    file           = request.files.get("image")
    img_filename   = save_image(file, UPLOAD_FOLDER)
    add_product(name, original_price, sale_price, description, img_filename)
    add_log(session.get(SESSION_AUTHO), "上架", None, name)
    flash("商品已上架", "success")
    return redirect(url_for("D.manage"))

def manage_clear_service():
    product_id = request.form.get("product_id")
    product    = get_product_by_id(product_id)
    soft_delete_product(product_id)
    add_log(session.get(SESSION_AUTHO), "刪除", product_id, product["name"])
    flash("商品已刪除", "success")
    return redirect(url_for("D.manage"))

def manage_service():
    products = get_all_products()
    return render_template("manage.html", products=products)

def manage_remove_service():
    product_id = request.form.get("product_id")
    product    = get_product_by_id(product_id)
    set_product_active(product_id, 0)
    add_log(session.get(SESSION_AUTHO), "下架", product_id, product["name"])
    flash("商品已下架", "success")
    return redirect(url_for("D.manage"))

def manage_restock_service():
    product_id = request.form.get("product_id")
    product    = get_product_by_id(product_id)
    set_product_active(product_id, 1)
    add_log(session.get(SESSION_AUTHO), "重新上架", product_id, product["name"])
    flash("商品已重新上架", "success")
    return redirect(url_for("D.manage"))

# 新增：商品修改服務（修改商品名稱、原價、特價、圖片）
def manage_edit_service():
    product_id     = request.form.get("product_id")
    name           = request.form.get("name")
    original_price = request.form.get("original_price")
    sale_price     = request.form.get("sale_price") or None  # 空字串轉 None，沒填特價就存 NULL
    file           = request.files.get("image")

    # 先確認商品存在，順便拿舊資料（特別是舊圖路徑，等下要刪）
    product = get_product_by_id(product_id)
    if not product:
        flash("找不到該商品", "error")
        return redirect(url_for("D.manage"))

    # 組要更新的資料
    update_data = {
        "name": name,
        "original_price": original_price,
        "sale_price": sale_price,
    }

    # 有上傳新圖才更新圖片欄位，沒上傳就保留原圖
    if file and file.filename != "":
        old_pic_path = product.get("product_pic")
        new_pic_path = save_image(file, UPLOAD_FOLDER)
        update_data["product_pic"] = new_pic_path
        del_imgae(old_pic_path)  # 刪掉舊圖避免堆積

    update_product(update_data, product_id)
    add_log(session.get(SESSION_AUTHO), "修改", product_id, name)
    flash("商品資料已更新", "success")
    return redirect(url_for("D.manage"))

def member_edit_service():
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

    if mobile and not validateMobile(mobile):
        flash("手機格式錯誤", "error")
        return redirect(url_for("D.member_edit"))

    update_data = {"user_name": name, "user_mobile": mobile}
   
    
    if file and file.filename != "":
        old_pic_path = getUser({"user_account":user_account}, "pic_path")
        new_pic_path = save_image(file, PROFILE_PIC_FOLDER, filename=user_account)
        update_data["pic_path"] = new_pic_path
        del_imgae(old_pic_path)
    
    updateUser(update_data, {"user_account": user_account})
    flash("資料更新成功", "success")
    return redirect(url_for("D.member"))

def member_service():
    user_account = session[SESSION_AUTHO]
    keyword = request.args.get("keyword", "").strip()
    
    if keyword:
        orders = search_orders(user_account, keyword)
    else:
        orders = get_orders(user_account)

    user = getUser(
        {"user_account": user_account},
        "user_name", "user_account", "user_email", "user_mobile"
    )
    user.update({"level": "一般會員"})
    return render_template("member.html",
        orders=orders,
        user=user,
        auth=get_auth(user_account)
    )

def manage_logout_service():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("B.index"))

def manage_log_service():
    return render_template("manage_log.html")
