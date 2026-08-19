'''
==========================================================
  Branch C — 購物車 & 結帳模組（Shopping_routers.py）
==========================================================

【負責範圍】
  Branch C 負責購物車、結帳等消費者購物流程。

【路由總覽】
  POST /cart/add                       加入購物車
  GET  /cart                           顯示購物車頁
  GET  /cart/remove/<item_id>          移除購物車中指定商品
  POST /cart/update                    即時更新購物車數量
  GET  /checkout                       顯示結帳表單
  POST /checkout                       送出訂單
  GET  /order/<order_id>/items         訂單明細 AJAX

  【綠界 ECPay 串接】
  POST /payment/ecpay/notify           綠界 server-to-server callback
                                       接收付款結果通知，更新訂單狀態
                                       【公開路徑，不需登入】

  POST /payment/ecpay/return           綠界瀏覽器跳回結果頁
                                       讓使用者看到付款結果，
                                       依訂單狀態跳到對應頁面
                                       【公開路徑，但會檢查訂單擁有者】

  GET  /payment/ecpay/result/<id>      付款結果中繼頁（極少用到）
                                       當綠界回跳時 callback 還沒到，
                                       顯示「請稍候」並輪詢訂單狀態

【安全機制】
  - /cart/* 和 /checkout 套用 @userRequired
  - /payment/ecpay/notify 公開路徑（綠界 server 無法登入），
    但會驗證 CheckMacValue 簽章，無效請求直接 reject
  - /payment/ecpay/return 公開路徑，但會比對訂單擁有者
==========================================================
'''
# __________________________________________內部模組_____________________________________
from flask import Blueprint, request

# _______________________________________自定義模組_______________________________________
from AuthDecorator import userRequired
from .Shopping_services import (cart_add_service,
                                cart_service,
                                cart_remove_service,
                                checkout_service,
                                cart_update_service,
                                order_items_service,
                                start_delivery_worker,
                                ecpay_notify_service,
                                ecpay_return_service,
                                payment_result_service)

# _______________________________________初始化___________________________________________
bp = Blueprint("C", __name__)


# ════════════════════════════════════════════════════════════════
#   關鍵保護：阻止綠界相關路由覆蓋 session cookie
# ════════════════════════════════════════════════════════════════
# 【為什麼需要】
# 綠界刷完卡會用 cross-site POST 跳回 /payment/ecpay/return。
# 瀏覽器因為 SameSite=Lax 不會把 session cookie 帶過去，
# 所以這個請求在 Flask 看來「使用者沒登入」，session 是空的。
#
# 然後 Flask 預設行為會把這個「空 session」寫回 cookie，
# 結果使用者原本的登入 cookie 就被覆蓋成空的 = 整個被登出。
#
# 【解法】
# 用 blueprint 的 after_request hook，攔截綠界相關路由的 response，
# 把 Flask 加上的 session Set-Cookie header 移除。
# 這樣使用者原本的 cookie 不會被覆蓋，登入狀態保留。
@bp.after_request
def _protect_session_on_ecpay_routes(response):
    # 只攔截綠界相關路由
    if request.path.startswith('/payment/ecpay/'):
        # 移除 Flask 加上的 session cookie（避免覆蓋使用者既有登入）
        cookies = response.headers.getlist('Set-Cookie')
        response.headers.pop('Set-Cookie', None)
        # 把非 session 的 cookie 保留下來
        for c in cookies:
            if not c.lower().startswith('session='):
                response.headers.add('Set-Cookie', c)
        print(f"[Session 保護] {request.path} 已過濾 session cookie")
    return response


# ════════════════════════════════════════════════════════════════
#   購物車 & 結帳
# ════════════════════════════════════════════════════════════════
@bp.route("/cart/add", methods=["POST"])
@userRequired
def cart_add():
    return cart_add_service()


@bp.route("/cart")
@userRequired
def cart():
    return cart_service()


@bp.route("/cart/remove/<int:item_id>")
@userRequired
def cart_remove(item_id):
    return cart_remove_service(item_id)


@bp.route("/cart/update", methods=["POST"])
@userRequired
def cart_update():
    return cart_update_service()


@bp.route("/checkout", methods=["GET", "POST"])
@userRequired
def checkout():
    return checkout_service()


@bp.route("/order/<int:order_id>/items", methods=["GET"])
@userRequired
def order_items(order_id):
    return order_items_service(order_id)


# ════════════════════════════════════════════════════════════════
#   綠界 ECPay 串接（公開路徑，不掛 @userRequired）
# ════════════════════════════════════════════════════════════════
# notify 是綠界 server 打過來的，根本沒 session，掛 userRequired 會直接 401。
# 安全靠 CheckMacValue 簽章驗證。
@bp.route("/payment/ecpay/notify", methods=["POST"])
def ecpay_notify():
    return ecpay_notify_service()


# return 是瀏覽器跳回來的，理論上 session 還在，但綠界的 POST 是 cross-site，
# 某些瀏覽器設定（SameSite=Strict）可能會把 session cookie 擋掉，
# 所以也不掛 userRequired，靠訂單擁有者比對確保安全。
@bp.route("/payment/ecpay/return", methods=["POST"])
def ecpay_return():
    return ecpay_return_service()


# result 是中繼頁（callback 比瀏覽器跳回慢時會用到）。
# 不掛 @userRequired，因為 cross-site POST 跳回後 session 會被 SameSite 擋掉。
# 安全靠「只顯示訂單狀態、不顯示敏感資訊」維持。
@bp.route("/payment/ecpay/result/<int:order_id>", methods=["GET"])
def payment_result(order_id):
    return payment_result_service(order_id)


# ______________________________________待發道具輪詢______________________________________
start_delivery_worker()
