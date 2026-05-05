# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from .Product_services import index_service,product_detail_service
from AuthDecorator import blockAdmin

# _______________________________________初始化___________________________________________
bp = Blueprint("B",__name__)

# ________________________________________API_____________________________________________

@bp.route("/")
@blockAdmin
def index():return index_service()

# 商品詳細頁
@bp.route("/product/<int:product_id>")
@blockAdmin
def product_detail(product_id):return product_detail_service(product_id)

