# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import adminRequired,userRequired
from .Management_services import (
    manage_add_service,manage_clear_service,manage_service,
    manage_remove_service,manage_restock_service,
    member_edit_service,member_service,
    manage_logout_service,manage_log_service,manage_edit_service,
    member_cards_service,add_card_service,delete_card_service,set_default_card_service,
    # 後台操作日誌(月份分組)的 partial
    manage_log_month_service,
    # 已完成訂單查詢
    manage_completed_orders_service,member_completed_orders_service,
    manage_order_items_service,member_order_items_service,
)

# _______________________________________初始化___________________________________________
bp = Blueprint("D",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/add", methods=["GET", "POST"])
@adminRequired
def manage_add():return manage_add_service()

@bp.route("/manage/clear", methods=["GET", "POST"])
@adminRequired
def manage_clear():return manage_clear_service()

@bp.route("/manage", methods=["GET"])
@adminRequired
def manage():return manage_service()

@bp.route("/manage/remove", methods=["GET", "POST"])
@adminRequired
def manage_remove():return manage_remove_service()

@bp.route("/manage/restock", methods=["GET", "POST"])
@adminRequired
def manage_restock():return manage_restock_service()

@bp.route("/manage/edit", methods=["GET", "POST"])
@adminRequired
def manage_edit():return manage_edit_service()

@bp.route("/member/edit", methods=["GET", "POST"])
@userRequired
def member_edit():return member_edit_service()

# 會員中心
@bp.route("/member")
@userRequired
def member():return member_service()

@bp.route("/manage/logout")
@adminRequired
def manage_logout():return manage_logout_service()

# ── 後台操作日誌(按月份分組) ─────────────────────────────────────────────
@bp.route("/manage/log")
@adminRequired
def manage_log():return manage_log_service()

# AJAX partial:取得指定月份的所有日誌紀錄
@bp.route("/manage/log/month/<month>", methods=["GET"])
@adminRequired
def manage_log_month(month):return manage_log_month_service(month)

# ── 信用卡管理 ──────────────────────────────────────────────────────────
@bp.route("/member/cards", methods=["GET"])
@userRequired
def member_cards():return member_cards_service()

@bp.route("/member/cards/add", methods=["GET", "POST"])
@userRequired
def add_card():return add_card_service()

@bp.route("/member/cards/delete", methods=["GET", "POST"])
@userRequired
def delete_card():return delete_card_service()

@bp.route("/member/cards/set_default", methods=["GET", "POST"])
@userRequired
def set_default_card_route():return set_default_card_service()

# ── 已完成訂單查詢(管理員 / 使用者) ────────────────────────────────────────
@bp.route("/manage/orders", methods=["GET"])
@adminRequired
def manage_completed_orders():return manage_completed_orders_service()

@bp.route("/manage/orders/<int:order_id>/items", methods=["GET"])
@adminRequired
def manage_order_items(order_id):return manage_order_items_service(order_id)

@bp.route("/member/orders", methods=["GET"])
@userRequired
def member_completed_orders():return member_completed_orders_service()

@bp.route("/member/orders/<int:order_id>/items", methods=["GET"])
@userRequired
def member_order_items(order_id):return member_order_items_service(order_id)
