# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash
from flask_mail import Mail, Message
from shutil import copy,move

# _______________________________________自定義模組_______________________________________
import settings

#測試用 - 從 .env 載入環境變數(如資料庫連線資訊、郵件帳密等)
from dotenv import load_dotenv
import os

from models import Models
 
# BranchC: 添加 validateEmail, validatePhone 正規格式驗證式函式
from AuthDecorator import guestOnly,tokenRequired,loginRequired, validateEmail, validatePhone, validateCreditCard
from utils import getRandomVerifyCode,getResponseForm,getResponseFile,getVerifyToken,checkUserInput


# _______________________________________初始化___________________________________________
app = Flask(__name__)
app.secret_key = settings.SESSION_KEY

load_dotenv()
settings.HOST     = os.getenv("DB_HOST")
settings.PORT     = int(os.getenv("DB_PORT"))
settings.USER     = os.getenv("DB_USER")
settings.PASSWORD = os.getenv("DB_PASSWORD")
settings.DATABASE = os.getenv("DB_DATABASE")


model = Models()

# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'cbes502034@gmail.com'
# app.config['MAIL_PASSWORD'] = "wqsemkvtjlzakidy"
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)

# 測試用
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS']  = False
app.config['MAIL_USE_SSL']  = True
mail = Mail(app)



# ________________________________________API_____________________________________________

# ── Branch A：首頁、註冊、登入、會員、找回帳密 ──────────────────────────────────────────

# 首頁：取得所有商品，已登入者額外傳入帳號與大頭貼資訊
@app.route("/")
def index():
    # 測試用，添加商品列表到首頁
    products = model.get_products()
    
    if session.get(settings.SESSION_AUTHO):
        return render_template("index.html",
                               
                               # 測試用，添加商品列表到首頁
                               products=products,
                               
                               auth={"logged_in":True,
                                     "account":session.get(settings.SESSION_AUTHO),
                                     "profile_pic":model.getUser({"user_account":session.get(settings.SESSION_AUTHO)}, "pic_path")
                                     })
    return render_template("index.html")


# 註冊：GET 顯示表單，POST 驗證輸入、建立帳號、複製預設大頭貼、發送驗證信
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
    
    # 測試用，信箱添加格式驗證（正規表示式）
    if not validateEmail(res_email):
        flash("信箱格式錯誤")
        return render_template("register.html")

    # 測試用，手機添加格式驗證（正規表示式）
    if not validatePhone(res_mobile):
        flash("手機格式錯誤")
        return render_template("register.html")

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
    

# 信箱驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後將大頭貼移至正式路徑並啟用帳號
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
    
    # 驗證成功：將大頭照從暫存移至正式路徑，並啟用帳號
    user_filename = f"{user_account}.{user_pic_path.rsplit('.',1)[-1]}"
    new_pic_path = settings.PROFILE_PIC_PATH.format(user_filename)
    move(user_pic_path,new_pic_path)
    
    model.updateUser({"verify_status":True,"pic_path":new_pic_path},{"token":token})
    
    flash("驗證成功")
    return render_template("login.html")
    
# 登入：GET 顯示表單，POST 驗證帳號/密碼/信箱與驗證狀態，成功後寫入 session
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


# 忘記密碼：GET 顯示表單，POST 驗證帳號與信箱後發送重設密碼驗證信
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
    
    # 產生新 token 與驗證碼，發送重設密碼驗證信
    token = getVerifyToken(32)
    model.updateUser({"token":token},{"user_account":res_account})

    code = getRandomVerifyCode(6)
    model.updateUser({"code":code},{"user_account":res_account})
    
    # msg = Message("重設密碼驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    
    # 測試用，發送重設密碼驗證信
    msg = Message("重設密碼驗證信", sender=os.getenv("MAIL_USERNAME"), recipients=[res_email])
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/login/find/password/email/{token}/verify/code">點擊此連結，即可重設密碼</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")


# 重設密碼驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後顯示重設密碼頁
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
    

# 重設密碼：POST 驗證新舊密碼不同且兩次輸入一致後更新密碼
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

    
# 找回帳號：GET 顯示表單，POST 以信箱查詢帳號並發送驗證信
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

    # msg = Message("取得帳號驗證信",sender="cbes502034@gmail.com",recipients=[res_email])
    
    # 測試用，發送取得帳號驗證信
    msg = Message("取得帳號驗證信", sender=os.getenv("MAIL_USERNAME"), recipients=[res_email])
    
    msg.html = f"""<div><a href="http://127.0.0.1:{settings.APP_PORT}/login/find/account/email/{token}/verify/code">點擊此連結，即可取得帳號</a></div>
                    <h2>驗證碼 : {code}</h2>
    """
    mail.send(msg)
    flash("驗證碼已發送完成，請至信箱中進行驗證程序")
    
    return render_template("login.html")


# 找回帳號驗證碼確認：POST 比對驗證碼，成功後以 flash 顯示帳號給使用者
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

# 登出：清除 session 中的登入資訊並導回首頁
@app.route("/logout")
@loginRequired
def logout():
    session.pop(settings.SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("index"))






# ── 會員中心 ──────────────────────────────────────────────────────────────────
@app.route("/member")
@loginRequired
def member():
    # 顯示目前登入使用者的歷史訂單
    # 若 URL 帶有 keyword 參數（如 /member?keyword=台北），
    # 則使用 LIKE % 搜尋地址或狀態欄位中包含關鍵字的訂單
    # 若無關鍵字，則顯示所有訂單
    user_account = session[settings.SESSION_AUTHO]
    keyword = request.args.get("keyword", "").strip()

    if keyword:
        members = model.search_orders(user_account, keyword)
    else:
        members = model.get_orders(user_account)

    user_name, user_email, user_mobile = model.getUser(
        {"user_account": user_account}, "user_name", "user_email", "user_mobile"
    )
    user = {
        'name'   : user_name,
        'account': user_account,
        'email'  : user_email,
        'phone'  : user_mobile,
        'level'  : '一般會員'
    }
    return render_template("member.html",
                           orders=members,
                           keyword=keyword,
                           user=user,
                           address=None,
                           auth={'logged_in': True, 
                                 'account': user_account,
                                 "profile_pic": model.getUser({"user_account": session.get(settings.SESSION_AUTHO)}, "pic_path")})


# ── Branch C：購物車 & 結帳 ───────────────────────────────────────────────────

@app.route("/cart")
@loginRequired
def cart():
    # 顯示購物車頁面
    # 從 session 取得登入帳號，查詢購物車商品，計算各項金額後傳給模板
    user_account = session[settings.SESSION_AUTHO]
    rows = model.get_cart_items(user_account)

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
                           auth={'logged_in': True,
                                 'account': user_account,
                                 "profile_pic": model.getUser({"user_account": session.get(settings.SESSION_AUTHO)}, "pic_path")})

@app.route("/cart/add", methods=["POST","GET"])
@loginRequired
def cart_add():
    # 新增商品到購物車，來自商品頁面的表單（POST）
    # 完成後導回來源頁（表單中的 next 欄位），預設導回購物車頁
    product_id = request.form.get("product_id") or request.args.get("product_id")
    if product_id:
        result = model.add_cart_item(session[settings.SESSION_AUTHO], int(product_id))
        if result:
            flash(f"「{result}」已加入購物車", "success")

    return redirect(request.form.get("next") or request.args.get("next") or url_for("cart"))


@app.route("/cart/remove/<int:item_id>")
@loginRequired
def cart_remove(item_id):
    # 從購物車移除指定商品（GET，對應模板中的 remove_url 連結）
    # 比對 user_account 確保只能刪自己的項目
    model.remove_cart_item(item_id, session[settings.SESSION_AUTHO])
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@loginRequired
def checkout():
    # 結帳頁面（GET）與送出訂單（POST）
    # GET：顯示商品清單與付款表單
    # POST：建立訂單、清空購物車，導向訂單列表頁
    user_account = session[settings.SESSION_AUTHO]
    rows = model.get_cart_items(user_account)

    if not rows:
        flash("購物車是空的")
        return redirect(url_for("cart"))

    if request.method == "POST":
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

        items = []
        total = 0
        for row in rows:
            item_total = row['price'] * row['quantity']
            total     += item_total
            items.append({
                'product_id': row['product_id'],
                'quantity'  : row['quantity'],
                'price'     : row['price'],
            })

        shipping = 60
        total   += shipping

        order_id = model.create_order(
            user_account, total, payment_method,
            delivery_method, address, note, items
        )
        model.clear_cart(user_account)

        flash(f"訂單 #{order_id} 建立成功！", "success")
        return redirect(url_for("member"))

    # GET：組裝模板所需的資料
    order_items = []
    subtotal    = 0
    for row in rows:
        item_total  = row['price'] * row['quantity']
        subtotal   += item_total
        order_items.append({
            'name' : row['name'],
            'qty'  : row['quantity'],
            'price': item_total,
        })

    shipping = 60
    total    = subtotal + shipping

    return render_template("checkout.html",
                           submit_url=url_for("checkout"),
                           order_items=order_items,
                           summary={'shipping': shipping, 'total': total},
                           payment_methods=["信用卡", "ATM 轉帳", "貨到付款"],
                           shipping_methods=["宅配到府", "超商取貨"],
                           form=None,
                           auth={'logged_in': True,
                                 'account': user_account,
                                 "profile_pic": model.getUser({"user_account": session.get(settings.SESSION_AUTHO)}, "pic_path")})

# ── 其他路由與功能 ─────────────────────────────────────────────────────────────
@app.route("/index")
@app.route("/index.html")
def index_redirect():
    return redirect(url_for("index"))

@app.route("/member.html")
def member_redirect():
    return redirect(url_for("member"))

@app.route("/cart.html")
def cart_redirect():
    return redirect(url_for("cart"))


@app.route("/order/<int:order_id>/cancel", methods=["POST"])
@loginRequired
def order_cancel(order_id):
    user_account = session[settings.SESSION_AUTHO]
    success = model.cancel_order(order_id, user_account)
    if success:
        flash("訂單已取消", "success")
    else:
        flash("無法取消此訂單", "error")
    return redirect(url_for("member"))


if __name__ == "__main__":
    """先於settings.py中設定APP_PORT"""
    app.run(debug=True, use_reloader=False, port=settings.APP_PORT)
