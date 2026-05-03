# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import loginRequired
from .Shopping_services import cart_add_service,cart_service,cart_remove_service,checkout_service,order_cancel_service

# _______________________________________初始化___________________________________________
bp = Blueprint("C",__name__)

# ________________________________________API_____________________________________________
@bp.route("/cart/add", methods=["POST", "GET"])
@loginRequired
def cart_add():return cart_add_service()


@bp.route("/cart")
@loginRequired
def cart():return cart_service()


@bp.route("/cart/remove/<int:item_id>")
@loginRequired
def cart_remove(item_id):return cart_remove_service(item_id)


@bp.route("/checkout", methods=["GET", "POST"])
@loginRequired
def checkout():return checkout_service()


@bp.route("/order/<int:order_id>/cancel", methods=["GET","POST"])
@loginRequired
def order_cancel(order_id):return order_cancel_service(order_id)
