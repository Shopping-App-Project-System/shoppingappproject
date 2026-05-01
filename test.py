# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash
from flask_mail import Message



# _______________________________________自定義模組_______________________________________
import settings
import models_shopping
from utils import getRandomVerifyCode,getResponseForm,getVerifyToken,checkUserInput, validatePhone, validateCreditCard,save_image, move_image,del_imgae,get_auth
from AuthDecorator import guestOnly,tokenRequired,loginRequired,adminRequired

from extension import init_mail
from modules.index_module import bp as index_bp
from modules.register_module import bp as register_bp
from modules.verify_register_module import bp as verify_register_bp
from modules.login_module import bp as login_bp
from modules.forgot_password_module import bp as forgot_password_bp

# _______________________________________初始化___________________________________________

app = Flask(__name__)


app.secret_key = settings.SESSION_KEY  # ← 加這行
app.config['MAIL_SERVER']=settings.MAIL_SERVER
app.config['MAIL_PORT'] = settings.MAIL_PORT
app.config['MAIL_USERNAME'] = settings.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = settings.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = settings.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = settings.MAIL_USE_SSL

init_mail(app)

# ________________________________________API_____________________________________________

#__________商品搜尋列__________

app.register_blueprint(index_bp)
app.register_blueprint(register_bp)
app.register_blueprint(verify_register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(forgot_password_bp)






# 重設密碼驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後顯示重設密碼頁
@app.route("/login/find/password/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def verify_password(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    
    res_code = getResponseForm(request.form, "code")
    user_code = models_shopping.getUser({"token":token},"code")
    if res_code == user_code:
        flash("驗證成功")
        return render_template("reset_password.html",token=token)
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/password/email/{token}/verify/code")
    

# 重設密碼：POST 驗證新舊密碼不同且兩次輸入一致後更新密碼
@app.route("/login/reset/password/<token>",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def reset_password(token):
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
    
    user_password = models_shopping.getUser({"token":token},"user_password")
    if res_password == user_password:
        flash("不可使用重複的密碼，請更新")
        return render_template("reset_password.html", token=token)
    
    models_shopping.updateUser({"user_password":res_password},{"token":token})
    flash("密碼更新成功")
    return render_template("login.html")

    
# 找回帳號：GET 顯示表單，POST 以信箱查詢帳號並發送驗證信
@app.route("/login/find/account",methods = ["POST","GET"])
@guestOnly
def find_account():
    if request.method == "GET":
        return render_template("find_account.html")

    msg = checkUserInput(request.form,email="信箱")
    if msg:
        flash("請輸入"+msg)
        return render_template("find_account.html")
    res_email = getResponseForm(request.form, "email")
    user_account = models_shopping.getUser({"user_email":res_email},"user_email")
    
    if user_account is None:
        flash("信箱輸入錯誤")
        return render_template("find_account.html")
    
    token = getVerifyToken(32)
    models_shopping.updateUser({"token":token},{"user_email":res_email})

    code = getRandomVerifyCode(6)
    models_shopping.updateUser({"code":code},{"user_email":res_email})

    # msg = Message("取得帳號驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    
    # 測試用，發送取得帳號驗證信
    msg = Message("取得帳號驗證信", sender=settings.MAIL_USERNAME, recipients=[res_email])
    
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")


# 找回帳號驗證碼確認：POST 比對驗證碼，成功後以 flash 顯示帳號給使用者
@app.route("/login/find/account/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def verify_account(token):
    if request.method == "GET":
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    msg = checkUserInput(request.form,code="驗證碼")
    if msg:
        flash("請輸入"+msg)
        return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

    res_code = getResponseForm(request.form, "code")
    user = models_shopping.getUser({"token":token},"code","user_account")
    user_code,user_account = user["code"],user["user_account"]
    if res_code == user_code:
        flash(f"您的帳號為{user_account}")
        return render_template("login.html")
    flash("驗證失敗")
    return render_template("verify_code.html",token=token,form_action=f"/login/find/account/email/{token}/verify/code")

# 登出：清除 session 中的登入資訊並導回首頁
@app.route("/logout")
@loginRequired
def logout():
    session.pop(settings.SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("index"))

#__________商品詳細頁__________
@app.route("/product/<int:id>")
def product_detail(id):
    # 向 Models 索取這三樣資料
    # product, stock, extra_pics = models_shopping.get_product_detail(id)
    product = models_shopping.get_product_by_id(id)
    
    # 如果沒找到商品，顯示 404
    if not product:
        return "找不到該商品", 404
    
    stock = models_shopping.get_product_stock(id)
    extra_pics = models_shopping.get_product_pics(id)
    return render_template(
        "product.html",
        product=product,
        stock=stock,
        extra_pics=extra_pics
    )



# ── 會員中心 ──────────────────────────────────────────────────────────────────
@app.route("/member")
@loginRequired
def member():
    user_account = session[settings.SESSION_AUTHO]
    keyword = request.args.get("keyword", "").strip()

    if keyword:
        orders = models_shopping.search_orders(user_account, keyword)
    else:
        orders = models_shopping.get_orders(user_account)

    user = models_shopping.getUser(
        {"user_account": user_account},
        "user_name", "user_account", "user_email", "user_mobile"
    )
    user.update({"level": "一般會員"})
    return render_template("member.html",
        orders=orders,
        user=user,
        auth=get_auth(user_account)
    )

@app.route("/member/edit", methods=["GET", "POST"])
@loginRequired
def member_edit():
    user_account = session.get(settings.SESSION_AUTHO)

    if request.method == "GET":
        user = models_shopping.getUser(
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
        old_pic_path = models_shopping.getUser({"user_account":user_account}, "pic_path")
        new_pic_path = save_image(file, settings.PROFILE_PIC_FOLDER, filename=user_account)
        update_data["pic_path"] = new_pic_path
        del_imgae(old_pic_path)
    
    models_shopping.updateUser(update_data, {"user_account": user_account})
    flash("資料更新成功", "success")
    return redirect(url_for("member"))

# ── Branch C：購物車 & 結帳 ───────────────────────────────────────────────────

@app.route("/cart")
@loginRequired
def cart():
    # 顯示購物車頁面
    # 從 session 取得登入帳號，查詢購物車商品，計算各項金額後傳給模板
    user_account = session[settings.SESSION_AUTHO]
    rows = models_shopping.get_cart_items(user_account)

    items    = []
    subtotal = 0
    for row in rows:
        item_total = row['price'] * row['quantity']
        subtotal  += item_total
        items.append({
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'remove_url': url_for('cart_remove', item_id=row['id']),
        })

    shipping = 60 if subtotal > 0 else 0
    discount = 0
    total    = subtotal + shipping - discount

    summary = {
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total'   : total,
    }

    return render_template("cart.html",
                           cart_items=items,
                           summary=summary,
                           checkout_url=url_for("checkout"),
                           auth=get_auth(user_account))

@app.route("/cart/add", methods=["POST", "GET"])
@loginRequired
def cart_add():
    if request.method == "GET":
        return redirect(url_for("cart"))

    next_url = request.form.get("next") or url_for("cart")
    product_id = request.form.get("product_id")

    if not product_id:
        return redirect(next_url)

    product = models_shopping.get_product(int(product_id))
    if not product:
        flash("商品不存在")
        return redirect(next_url)

    models_shopping.upsert_cart(session[settings.SESSION_AUTHO], int(product_id))
    flash(f"「{product['name']}」已加入購物車", "success")
    return redirect(next_url)


@app.route("/cart/remove/<int:item_id>")
@loginRequired
def cart_remove(item_id):
    # 從購物車移除指定商品（GET，對應模板中的 remove_url 連結）
    # 比對 user_account 確保只能刪自己的項目
    models_shopping.remove_cart_item(item_id, session[settings.SESSION_AUTHO])
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@loginRequired
def checkout():
    user_account = session.get(settings.SESSION_AUTHO)
    rows = models_shopping.get_cart_items(user_account)

    if not rows:
        flash("購物車是空的")
        return redirect(url_for("cart"))

    if request.method == "GET":
        user = models_shopping.getUser(
            {"user_account": user_account},
            "user_name", "user_mobile", "user_address"
        )

        order_items = []
        subtotal    = 0
        for row in rows:
            item_total  = row['price'] * row['quantity']
            subtotal   += item_total
            order_items.append({
                "name" : row['name'],
                "qty"  : row['quantity'],
                "price": item_total,
            })

        shipping = 60
        total    = subtotal + shipping

        return render_template("checkout.html",
            submit_url=url_for("checkout"),
            order_items=order_items,
            summary={"shipping": shipping, "total": total},
            payment_methods=["信用卡", "ATM 轉帳", "貨到付款"],
            shipping_methods=["宅配到府", "超商取貨"],
            form={
                "name"   : user.get("user_name"),
                "phone"  : user.get("user_mobile"),
                "address": user.get("user_address")
            },
            auth=get_auth(user_account)
        )

    name            = request.form.get("name", "")
    phone           = request.form.get("phone", "")
    address         = request.form.get("address", "")
    payment_method  = request.form.get("payment", "")
    delivery_method = request.form.get("shipping", "")
    note            = request.form.get("note", "")
    card_number     = request.form.get("card_number", "")

    if phone and not validatePhone(phone):
        flash("手機格式錯誤，請輸入09開頭的10位數字", "error")
        return redirect(url_for("checkout"))

    if payment_method == "信用卡":
        if not card_number:
            flash("請輸入信用卡卡號", "error")
            return redirect(url_for("checkout"))
        if not validateCreditCard(card_number):
            flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
            return redirect(url_for("checkout"))

    total    = sum(row['price'] * row['quantity'] for row in rows) + 60
    order_id = models_shopping.insert_order(user_account, total, payment_method, delivery_method, address, note)
    for row in rows:
        models_shopping.insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])
    
    models_shopping.clear_cart(user_account)
    flash(f"訂單 #{order_id} 建立成功！", "success")
    return redirect(url_for("member"))

@app.route("/order/<int:order_id>/cancel", methods=["GET","POST"])
@loginRequired
def order_cancel(order_id):
    if request.method == "GET":
        return redirect(url_for("index"))
    user_account = session[settings.SESSION_AUTHO]
    
    order = models_shopping.get_order(order_id, user_account)
    if not order:
        flash("訂單不存在")
        return redirect(url_for("member"))
    
    models_shopping.cancel_order(order_id)
    flash("訂單已取消", "success")
    return redirect(url_for("member"))

# ___________________________________________________________________________
@app.route("/manage", methods=["GET"])
@adminRequired
def manage():
    products = models_shopping.get_all_products()
    return render_template("manage.html", products=products)

@app.route("/manage/add", methods=["POST"])
@adminRequired
def manage_add():
    name         = request.form.get("name")
    price        = request.form.get("price")
    description  = request.form.get("description")
    file         = request.files.get("image")
    img_filename = save_image(file, settings.UPLOAD_FOLDER)
    models_shopping.add_product(name, price, description, img_filename)
    models_shopping.add_log(session.get(settings.SESSION_AUTHO), "上架", None, name)
    flash("商品已上架", "success")
    return redirect(url_for("manage"))

@app.route("/manage/remove", methods=["POST"])
@adminRequired
def manage_remove():
    product_id = request.form.get("product_id")
    product    = models_shopping.get_product_by_id(product_id)
    models_shopping.set_product_active(product_id, 0)
    models_shopping.add_log(session.get(settings.SESSION_AUTHO), "下架", product_id, product["name"])
    flash("商品已下架", "success")
    return redirect(url_for("manage"))

@app.route("/manage/clear", methods=["POST"])
@adminRequired
def manage_clear():
    product_id = request.form.get("product_id")
    product    = models_shopping.get_product_by_id(product_id)
    models_shopping.soft_delete_product(product_id)
    models_shopping.add_log(session.get(settings.SESSION_AUTHO), "刪除", product_id, product["name"])
    flash("商品已刪除", "success")
    return redirect(url_for("manage"))

@app.route("/manage/restore", methods=["POST"])
@adminRequired
def manage_restore():
    product_id = request.form.get("product_id")
    product    = models_shopping.get_product_by_id(product_id)
    models_shopping.restore_product(product_id)
    models_shopping.add_log(session.get(settings.SESSION_AUTHO), "恢復", product_id, product["name"])
    flash("商品已恢復", "success")
    return redirect(url_for("manage"))

@app.route("/manage/restock", methods=["POST"])
@adminRequired
def manage_restock():
    product_id = request.form.get("product_id")
    product    = models_shopping.get_product_by_id(product_id)
    models_shopping.set_product_active(product_id, 1)
    models_shopping.add_log(session.get(settings.SESSION_AUTHO), "重新上架", product_id, product["name"])
    flash("商品已重新上架", "success")
    return redirect(url_for("manage"))

if __name__ == "__main__":
    """先於settings.py中設定APP_PORT"""
    app.run(debug=True,use_reloader=False,port=settings.APP_PORT)
