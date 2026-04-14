from flask import request, redirect, render_template, session, url_for, flash
import settings

'''
# 測試用，整合前移除
from dotenv import load_dotenv
import os

load_dotenv(r"D:\Python\Workspace\acer\小組專題\T1\.env")

settings.HOST     = os.getenv("DB_HOST")
settings.PORT     = int(os.getenv("DB_PORT", 3306))
settings.USER     = os.getenv("DB_USER")
settings.PASSWORD = os.getenv("DB_PASSWORD")
settings.DATABASE = os.getenv("DB_DATABASE")
'''

def register(app, model):
    # 將 Branch C 的所有路由註冊到 Flask app 上
    # 在 controler.py 呼叫 cart_checkout.register(app, model) 即可掛載

    '''
    # 測試用，整合前移除
    @app.route("/dev-login")
    def dev_login():
        session[settings.SESSION_AUTHO] = "test_user"
        try:
            import mariadb
            conn = mariadb.connect(host=settings.HOST, port=settings.PORT,
                                   user=settings.USER, password=settings.PASSWORD,
                                   database=settings.DATABASE)
            conn.close()
            db_status = "DB 連線成功"
        except Exception as e:
            db_status = f"DB 連線失敗：{e}"
        return f"已模擬登入｜{db_status}"

    # 測試用，整合前移除
    @app.route("/dev-add/<int:product_id>")
    def dev_add(product_id):
        if settings.SESSION_AUTHO not in session:
            return "請先去 /dev-login"
        model.add_cart_item(session[settings.SESSION_AUTHO], product_id)
        return redirect(url_for("cart"))
    '''

    @app.route("/cart")
    def cart():
        # 顯示購物車頁面
        # 從 session 取得登入帳號，查詢購物車商品，計算各項金額後傳給模板
        if settings.SESSION_AUTHO not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        user_account = session[settings.SESSION_AUTHO]
        rows = model.get_cart_items(user_account)

        items = []
        subtotal = 0
        for row in rows:
            item_total = row['price'] * row['quantity']
            subtotal += item_total
            items.append({
                'image':      row['image_path'],
                'name':       row['name'],
                'qty':        row['quantity'],
                'price':      row['price'],
                'remove_url': url_for('cart_remove', item_id=row['id']),
            })

        shipping = 60 if subtotal > 0 else 0
        discount = 0
        total = subtotal + shipping - discount

        summary = {
            'subtotal': subtotal,
            'shipping': shipping,
            'discount': discount,
            'total':    total,
        }

        return render_template("cart.html",
                               cart_items=items,
                               summary=summary,
                               checkout_url=url_for("checkout"))

    @app.route("/cart/add", methods=["POST"])
    def cart_add():
        # 新增商品到購物車，來自商品頁面的表單（POST）
        # 完成後導回來源頁（表單中的 next 欄位），預設導回購物車頁
        if settings.SESSION_AUTHO not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        product_id = request.form.get("product_id")
        if product_id:
            model.add_cart_item(session[settings.SESSION_AUTHO], int(product_id))

        return redirect(request.form.get("next") or url_for("cart"))

    @app.route("/cart/remove/<int:item_id>")
    def cart_remove(item_id):
        # 從購物車移除指定商品（GET，對應模板中的 remove_url 連結）
        # 比對 user_account 確保只能刪自己的項目
        if settings.SESSION_AUTHO not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        model.remove_cart_item(item_id, session[settings.SESSION_AUTHO])
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        # 結帳頁面（GET）與送出訂單（POST）
        # GET：顯示商品清單與付款表單
        # POST：建立訂單、清空購物車，導向訂單列表頁
        if settings.SESSION_AUTHO not in session:
            flash("請先登入")
            return redirect(url_for("login"))

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

            items = []
            total = 0
            for row in rows:
                item_total = row['price'] * row['quantity']
                total += item_total
                items.append({
                    'product_id': row['product_id'],
                    'quantity':   row['quantity'],
                    'price':      row['price'],
                })

            shipping = 60
            total += shipping

            order_id = model.create_order(
                user_account, total, payment_method,
                delivery_method, address, note, items
            )
            model.clear_cart(user_account)

            flash(f"訂單 #{order_id} 建立成功！")
            return redirect(url_for("order_list"))

        # GET：組裝模板所需的資料
        order_items = []
        subtotal = 0
        for row in rows:
            item_total = row['price'] * row['quantity']
            subtotal += item_total
            order_items.append({
                'name':  row['name'],
                'qty':   row['quantity'],
                'price': item_total,
            })

        shipping = 60
        total = subtotal + shipping

        return render_template("checkout.html",
                               submit_url=url_for("checkout"),
                               order_items=order_items,
                               summary={'shipping': shipping, 'total': total},
                               payment_methods=["信用卡", "ATM 轉帳", "貨到付款"],
                               shipping_methods=["宅配到府", "超商取貨"],
                               form=None)

    @app.route("/orders")
    def order_list():
        # 顯示目前登入使用者的歷史訂單
        # 若 URL 帶有 keyword 參數（如 /orders?keyword=台北），
        # 則使用 LIKE % 搜尋地址或狀態欄位中包含關鍵字的訂單
        # 若無關鍵字，則顯示所有訂單
        if settings.SESSION_AUTHO not in session:
            flash("請先登入")
            return redirect(url_for("login"))

        user_account = session[settings.SESSION_AUTHO]
        keyword = request.args.get("keyword", "").strip()

        if keyword:
            orders = model.search_orders(user_account, keyword)
        else:
            orders = model.get_orders(user_account)

        # 目前暫以 session 帳號填入
        user = {'name': user_account, 'account': user_account,
                'email': '', 'phone': '', 'level': '一般會員'}
        return render_template("member.html", orders=orders, keyword=keyword,
                               user=user, address=None,
                               cart_url=url_for("cart"),
                               member_url=url_for("order_list"),
                               home_url="/")
