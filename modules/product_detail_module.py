# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import get_product_by_id,get_product_stock,get_product_pics

# _______________________________________初始化___________________________________________
bp = Blueprint("product_detail",__name__)

# ________________________________________API_____________________________________________
# 商品詳細頁
@bp.route("/product/<int:id>")
def product_detail(id):
    # 向 Models 索取這三樣資料
    # product, stock, extra_pics = models_shopping.get_product_detail(id)
    product = get_product_by_id(id)
    
    # 如果沒找到商品，顯示 404
    if not product:
        return "找不到該商品", 404
    
    stock = get_product_stock(id)
    extra_pics = get_product_pics(id)
    return render_template(
        "product.html",
        product=product,
        stock=stock,
        extra_pics=extra_pics
    )


