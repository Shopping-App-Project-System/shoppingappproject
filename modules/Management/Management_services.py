# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash

# _______________________________________自定義模組_______________________________________
from models import (
    getUser,updateUser,
    add_product,add_log,get_product_by_id,soft_delete_product,
    get_all_products,set_product_active,
    search_orders,get_orders,update_product,
    get_member_cards,add_member_card,delete_member_card,set_default_card,clear_default_cards,
    get_all_categories,add_product_stock
)
from settings import SESSION_AUTHO,UPLOAD_FOLDER,PROFILE_PIC_FOLDER
from utils import get_auth,validateMobile,save_image,del_imgae,requestParsor
# _______________________________________初始化___________________________________________

# _______________________________________services___________________________________________
@requestParsor
def manage_add_service(name,original_price,sale_price,description,image,product_quantity):
    img_filename   = save_image(image, UPLOAD_FOLDER)
    product_id = add_product(name, original_price, sale_price, description, img_filename)
    add_product_stock(product_id,int(product_quantity))
    add_log(session.get(SESSION_AUTHO), "上架", product_id, name)
    flash("商品已上架", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def manage_clear_service(product_id):
    product    = get_product_by_id(product_id)
    soft_delete_product(product_id)
    add_log(session.get(SESSION_AUTHO), "刪除", product_id, product["name"])
    flash("商品已刪除", "success")
    return redirect(url_for("D.manage"))

def manage_service():
    products = get_all_products()
    categories = get_all_categories()
    return render_template("manage.html", products=products, category_list = categories)

@requestParsor
def manage_remove_service(product_id):
    product    = get_product_by_id(product_id)
    set_product_active(product_id, 0)
    add_log(session.get(SESSION_AUTHO), "下架", product_id, product["name"])
    flash("商品已下架", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def manage_restock_service(product_id):
    product    = get_product_by_id(product_id)
    set_product_active(product_id, 1)
    add_log(session.get(SESSION_AUTHO), "重新上架", product_id, product["name"])
    flash("商品已重新上架", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def manage_edit_service(product_id,name,original_price,sale_price,image,product_pic):
    '''這裡少一個GET method 補上後即可跳至網頁 同時要新增一張修改頁面 或者也可以畫面上直接操作'''
    # if request.method == "GET":
    #     return render_template()
    product = get_product_by_id(product_id)
    if not product:
        flash("找不到該商品", "error")
        return redirect(url_for("D.manage"))

    update_data = {
        "name": name,
        "original_price": original_price,
        "sale_price": sale_price,
    }

    if image and image.filename != "":
        new_pic_path = save_image(image, UPLOAD_FOLDER)
        update_data["product_pic"] = new_pic_path
        del_imgae(product_pic)

    update_product(update_data, product_id)
    add_log(session.get(SESSION_AUTHO), "修改", product_id, name)
    flash("商品資料已更新", "success")
    return redirect(url_for("D.manage"))

def manage_logout_service():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("B.index"))

def manage_log_service():
    return render_template("manage_log.html")

@requestParsor
def member_edit_service(name,mobile,profile_pic):
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

    if mobile and not validateMobile(mobile):
        flash("手機格式錯誤", "error")
        return redirect(url_for("D.member_edit"))

    update_data = {"user_name": name, "user_mobile": mobile}

    if profile_pic and profile_pic.filename != "":
        old_pic_path = getUser({"user_account":user_account}, "pic_path")
        new_pic_path = save_image(profile_pic, PROFILE_PIC_FOLDER, filename=user_account)
        update_data["pic_path"] = new_pic_path
        del_imgae(old_pic_path)

    updateUser(update_data, {"user_account": user_account})
    flash("資料更新成功", "success")
    return redirect(url_for("D.member"))

@requestParsor
def member_service(keyword=""):
    user_account = session[SESSION_AUTHO]
    
    keyword = keyword.strip()
    if keyword:
        orders = search_orders(user_account, keyword)
    else:
        orders = get_orders(user_account)

    user = getUser(
        {"user_account": user_account},
        "user_name", "user_account", "user_email", "user_mobile"
    )
    user.update({"level": "一般會員"})

    # 同時把預設卡資訊塞到 user 物件裡，給 member.html 顯示「我的付款方式」摘要
    cards = get_member_cards(user_account)
    default_card = next((c for c in cards if c.get("is_default")), None)

    return render_template("member.html",
        orders=orders,
        user=user,
        auth=get_auth(user_account),
        default_card=default_card,
        card_count=len(cards)
    )

# ── 信用卡管理 services ────────────────────────────────────────────────────
# ⚠️ 注意：本功能直接儲存完整卡號，僅適用於學校作業/示意用途。

def member_cards_service():
    """信用卡管理頁：列出該會員所有信用卡。"""
    user_account = session[SESSION_AUTHO]
    cards = get_member_cards(user_account)
    return render_template("member_cards.html",
        cards=cards,
        auth=get_auth(user_account)
    )

@requestParsor
def add_card_service(is_default,card_number="",expiry="",holder_name=""):
    """新增一張信用卡。"""
    user_account = session[SESSION_AUTHO]
    card_number,expiry,holder_name = card_number.strip(),expiry.strip(),holder_name.strip()
    
    is_default   = 1 if is_default else 0

    # 簡易驗證（學校作業夠用）
    if not card_number or not expiry or not holder_name:
        flash("請完整填寫卡片資訊", "error")
        return redirect(url_for("D.member_cards"))

    # 卡號可能含空白或減號，去除後檢查長度
    cleaned_number = card_number.replace(" ", "").replace("-", "")
    if not cleaned_number.isdigit() or len(cleaned_number) != 16:
        flash("卡號必須為 16 碼數字", "error")
        return redirect(url_for("D.member_cards"))

    # 如果這是該會員的第一張卡，自動設為預設
    existing_cards = get_member_cards(user_account)
    if not existing_cards:
        is_default = 1
    
    if is_default:
        clear_default_cards(user_account)
    
    add_member_card(user_account, cleaned_number, expiry, holder_name, is_default)
    flash("信用卡已新增", "success")
    return redirect(url_for("D.member_cards"))

@requestParsor
def delete_card_service(card_id):
    """刪除一張信用卡。"""
    user_account = session[SESSION_AUTHO]
    delete_member_card(user_account, card_id)
    flash("信用卡已刪除", "success")
    return redirect(url_for("D.member_cards"))

@requestParsor
def set_default_card_service(card_id):
    """把指定卡設為預設。"""
    user_account = session[SESSION_AUTHO]
    clear_default_cards(user_account)
    set_default_card(user_account, card_id)
    flash("已設定為預設卡", "success")
    return redirect(url_for("D.member_cards"))
