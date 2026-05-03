# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import adminRequired,loginRequired
from .Management_services import manage_add_service,manage_clear_service,manage_service,manage_remove_service,manage_restock_service,member_edit_service,member_service,manage_logout_service

# _______________________________________初始化___________________________________________
bp = Blueprint("D",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/add", methods=["POST"])
@adminRequired
def manage_add():return manage_add_service()

@bp.route("/manage/clear", methods=["POST"])
@adminRequired
def manage_clear():return manage_clear_service()

@bp.route("/manage", methods=["GET"])
@adminRequired
def manage():return manage_service()

@bp.route("/manage/remove", methods=["POST"])
@adminRequired
def manage_remove():return manage_remove_service()

@bp.route("/manage/restock", methods=["POST"])
@adminRequired
def manage_restock():return manage_restock_service()

@bp.route("/member/edit", methods=["GET", "POST"])
@adminRequired
def member_edit():return member_edit_service()

# 會員中心
@bp.route("/member")
@adminRequired
def member():return member_service()

@bp.route("/manage/logout")
@adminRequired
def manage_logout():return manage_logout_service()