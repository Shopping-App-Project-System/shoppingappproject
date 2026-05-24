# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import adminRequired,userRequired
from .Management_services import (
    manage_add_service,manage_service,
    manage_remove_service,manage_restock_service,
    member_edit_service,member_service,
    manage_logout_service,manage_log_service,manage_edit_service,
    # 永久刪除功能已停用 (manage_clear_service)
    # manage_clear_service,
    # 後台操作日誌(月份分組)的 partial
    manage_log_month_service,
    # 已完成訂單查詢
    manage_completed_orders_service,member_completed_orders_service,
    manage_order_items_service,member_order_items_service,
    # 後台儀表板 (圖表)
    manage_dashboard_service,manage_dashboard_data_service,
)

# _______________________________________初始化___________________________________________
bp = Blueprint("D",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/add", methods=["GET", "POST"])
@adminRequired
def manage_add():return manage_add_service()

# 永久刪除路由已停用 (有訂單的商品因外鍵約束無法 hard delete,
# 沒訂單的商品用「下架」即可,故整段註解保留以備將來恢復).
# @bp.route("/manage/clear", methods=["GET", "POST"])
# @adminRequired
# def manage_clear():return manage_clear_service()

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

# ── 後台儀表板 (銷售統計圖表) ────────────────────────────────────────────
# 頁面:HTML 框架,只負責畫板子
@bp.route("/manage/dashboard", methods=["GET"])
@adminRequired
def manage_dashboard():return manage_dashboard_service()

# 資料 API:回傳 JSON,給前端 Chart.js 繪圖用
@bp.route("/manage/dashboard/data", methods=["GET"])
@adminRequired
def manage_dashboard_data():return manage_dashboard_data_service()
