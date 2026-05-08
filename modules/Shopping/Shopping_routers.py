'''
==========================================================
  Branch C — 購物車 & 結帳模組（Shopping_routers.py）
==========================================================

【負責範圍】
  Branch C 負責購物車、結帳、訂單取消等消費者購物流程。

【路由總覽】
  POST /cart/add
      加入購物車。
      驗證商品存在、未下架、庫存足夠，且加入後不超過庫存上限。
      僅接受 POST（防止直接以網址觸發）。

  GET  /cart
      顯示購物車頁面。
      列出所有購物車商品，計算小計、運費、折扣、總金額。

  GET  /cart/remove/<item_id>
      移除購物車中指定商品。

  GET  /checkout
      顯示結帳表單，帶入使用者基本資料與已儲存的信用卡清單。

  POST /checkout
      送出訂單。
      驗證必填欄位（姓名、地址、付款方式、配送方式）、
      手機格式、信用卡卡號格式、
      結帳前再次確認庫存是否足夠（防止購物車殘留舊資料超量），
      建立訂單與訂單明細，扣減庫存，清空購物車。

  POST /order/<order_id>/cancel
      取消指定訂單（僅限「處理中」狀態且屬於本人）。
      取消後自動將該訂單的所有商品庫存補回。

【安全機制】
  - 所有路由皆套用 @userRequired，未登入自動導向登入頁，
    管理員帳號導向後台，不開放一般購物流程。
  - 結帳總金額在後端重新計算，防止前端竄改價格。
  - 信用卡 card_id 驗證所有權，防止偽造請求使用他人卡片。
==========================================================
'''
# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import userRequired
from .Shopping_services import (cart_add_service,
                                cart_service,
                                cart_remove_service,
                                checkout_service,
                                order_cancel_service,
                                cart_update_service)

# _______________________________________初始化___________________________________________
bp = Blueprint("C",__name__)

# ________________________________________API_____________________________________________
@bp.route("/cart/add", methods=["POST"])
@userRequired
def cart_add():return cart_add_service()


@bp.route("/cart")
@userRequired
def cart():return cart_service()


@bp.route("/cart/remove/<int:item_id>")
@userRequired
def cart_remove(item_id):return cart_remove_service(item_id)

@bp.route("/cart/update", methods=["GET","POST"])
@userRequired
def cart_update():return cart_update_service()

@bp.route("/checkout", methods=["GET", "POST"])
@userRequired
def checkout():return checkout_service()


@bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@userRequired
def order_cancel(order_id):return order_cancel_service(order_id)
