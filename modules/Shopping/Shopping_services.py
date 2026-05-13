'''
==========================================================
  Branch C — 購物車 & 結帳模組（Shopping_services.py）
==========================================================

【功能清單】
  1. 加入購物車（cart_add_service）
  2. 購物車頁面（cart_service）
  3. 移除購物車商品（cart_remove_service）
  4. 購物車數量更新（cart_update_service）
  5. 結帳頁面 GET（checkout_service）
  6. 結帳送出 POST（checkout_service）
  7. 訂單明細查詢 API（order_items_service）

【資料表依賴】
 cart_items、orders、order_items、products、
 product_stock、member_cards、users
==========================================================
'''

# __________________________________________內部模組_____________________________________
from flask import request, redirect, render_template, session, url_for, flash

# _______________________________________自定義模組_______________________________________
from settings import SESSION_AUTHO
from utils import get_auth, validateCreditCard, requestParsor

# 【修改說明】
# notify_player 和 give_item 原本從 models import，
# 但 models 是放資料庫操作的，RCON 功能不應該放那裡。
# 改成從 mc_bridge 直接 import，邏輯更清晰。
from mc_bridge import notify_player, give_item

from models import (get_product_by_id,
                    get_product_stock,
                    find_cart_item,
                    upsert_cart,
                    get_cart_items,
                    remove_cart_item,
                    insert_order,
                    insert_order_item,
                    get_order_items_detail,
                    clear_cart,
                    get_member_cards,
                    deduct_product_stock,
                    get_cart_item_stock,
                    update_cart_qty,
                    get_user_order_seq)


# ── 加入購物車 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/add
@requestParsor
def cart_add_service(product_id=None, next=""):
    next_url = next or url_for("C.cart")

    if not product_id:
        return redirect(next_url)

    product = get_product_by_id(int(product_id))
    if not product:
        flash("商品不存在", "error")
        return redirect(next_url)
    if not product.get("is_active"):
        flash("此商品已下架", "error")
        return redirect(next_url)
    stock = get_product_stock(int(product_id))
    if not stock or stock.get("product_quantity", 0) <= 0:
        flash("此商品已無庫存", "error")
        return redirect(next_url)
    cart_item = find_cart_item(session[SESSION_AUTHO], int(product_id))
    current_qty = cart_item["quantity"] if cart_item else 0
    if current_qty + 1 > stock.get("product_quantity", 0):
        flash("購物車數量已達庫存上限", "error")
        return redirect(next_url)

    upsert_cart(session[SESSION_AUTHO], int(product_id))
    flash(f"「{product['name']}」已加入購物車", "success")
    return redirect(next_url)


# ── 購物車頁面 ────────────────────────────────────────────────────────────────────────────────
# 對應路由：GET /cart
def cart_service():
    user_account = session[SESSION_AUTHO]
    rows = get_cart_items(user_account)

    items    = []
    subtotal = 0
    for row in rows:
        item_total = row['price'] * row['quantity']
        subtotal  += item_total
        items.append({
            'id'        : row['id'],
            'image'     : row['image_path'],
            'name'      : row['name'],
            'qty'       : row['quantity'],
            'price'     : row['price'],
            'remove_url': url_for('C.cart_remove', item_id=row['id']),
            'stock'     : row['stock'],
            'is_active' : row['is_active'],
        })

    discount = 0
    total    = subtotal - discount

    summary = {
        'subtotal': subtotal,
        'discount': discount,
        'total'   : total,
    }

    return render_template("cart.html",
                           cart_items=items,
                           summary=summary,
                           checkout_url=url_for("C.checkout"),
                           auth=get_auth(user_account))


# ── 移除購物車商品 ────────────────────────────────────────────────────────────────────────────
# 對應路由：GET /cart/remove/<item_id>
def cart_remove_service(item_id):
    remove_cart_item(item_id, session[SESSION_AUTHO])
    return redirect(url_for("C.cart"))


# ── 購物車數量更新 ────────────────────────────────────────────────────────────────────────────
# 對應路由：POST /cart/update
@requestParsor
def cart_update_service(item_id, qty):
    user_account = session.get(SESSION_AUTHO)
    stock = get_cart_item_stock(item_id, user_account)
    if not stock or int(qty) > stock:
        return '', 400
    update_cart_qty(item_id, int(qty))
    return '', 200


# ── 結帳 ──────────────────────────────────────────────────────────────────────────────────────
# 對應路由：GET + POST /checkout
@requestParsor
def checkout_service(payment="", note="", card_id="", card_number=""):
    user_account = session.get(SESSION_AUTHO)
    rows = get_cart_items(user_account)

    if not rows:
        flash("購物車是空的", "error")
        return redirect(url_for("C.cart"))

    if request.method == "GET":
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

        saved_cards = get_member_cards(user_account)

        return render_template("checkout.html",
            submit_url=url_for("C.checkout"),
            order_items=order_items,
            summary={"total": subtotal},
            payment_methods=["ATM 轉帳", "信用卡"],
            saved_cards=saved_cards,
            auth=get_auth(user_account)
        )

    # ── POST：驗證表單並建立訂單 ──
    if not payment:
        flash("請選擇付款方式", "error")
        return redirect(url_for("C.checkout"))

    credit_card_number = None
    if payment == "信用卡":
        if card_id:
            saved_cards = get_member_cards(user_account)
            matched = next((c for c in saved_cards if str(c["id"]) == card_id), None)
            if not matched:
                flash("所選信用卡不存在", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = matched["card_number"][-4:]
        else:
            if not card_number:
                flash("請輸入信用卡卡號", "error")
                return redirect(url_for("C.checkout"))
            if not validateCreditCard(card_number):
                flash("信用卡卡號格式錯誤，請輸入16位數字", "error")
                return redirect(url_for("C.checkout"))
            credit_card_number = card_number.replace(" ", "")[-4:]

    for row in rows:                    # 結帳前重新確認商品狀態與庫存
        product = get_product_by_id(row["product_id"])
        if not product or not product.get("is_active"):
            flash(f"「{row['name']}」已下架，請回購物車移除後再結帳", "error")
            return redirect(url_for("C.cart"))
        stock     = get_product_stock(row["product_id"])
        available = stock.get("product_quantity", 0) if stock else 0
        if row["quantity"] > available:
            flash(f"「{row['name']}」庫存不足（剩餘 {available} 件），請回購物車調整數量", "error")
            return redirect(url_for("C.cart"))

    total    = sum(row['price'] * row['quantity'] for row in rows)
    order_id = insert_order(user_account, total, payment, note, credit_card_number)
    order_seq = get_user_order_seq(user_account, order_id)
    # 逐筆將購物車商品寫入訂單明細、扣庫存、發放道具
    for row in rows:
        insert_order_item(order_id, row["product_id"], row['quantity'], row['price'])
        # 扣減庫存
        deduct_product_stock(row["product_id"], row['quantity'])
        # 查出商品的 MC 道具 ID，直接發道具進背包
        product = get_product_by_id(row["product_id"])
        mc_item_id = product.get("mc_item_id")
        if mc_item_id:
            give_item(user_account, mc_item_id, row["quantity"])
            notify_player(user_account, f"✅ 訂單 #{order_seq} 已發放:{product['name']} x{row['quantity']}")

    # 清空購物車
    clear_cart(user_account)
    notify_player(user_account, f"訂單 #{order_seq} 建立成功!感謝購買!")
    flash("訂單建立成功！", "success")
    return redirect(url_for("D.member"))


# ── 訂單明細（AJAX）──────────────────────────────────────────────────────────────────────────
# 對應路由：GET /order/<order_id>/items
def order_items_service(order_id):
    # 回傳指定訂單的商品清單，供前端動態顯示訂單明細使用
    from flask import jsonify
    rows = get_order_items_detail(order_id)
    result = [
        {
            "name"   : r["name"],
            "qty"    : r["quantity"],
            "price"  : r["price"],
            "image"  : r["product_pic"] or "",
        }
        for r in rows
    ]
    return jsonify(result)


