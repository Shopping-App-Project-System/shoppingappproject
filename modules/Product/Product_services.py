# __________________________________________內部模組_____________________________________
from flask import request,render_template,session

# _______________________________________自定義模組_______________________________________
from models import search_categories,get_all_categories,get_product_by_id,get_product_stock,get_product_pics
from settings import SESSION_AUTHO
from utils import get_auth

# _______________________________________初始化___________________________________________


# ________________________________________services_____________________________________________
def index_service():
    cat_id = request.args.get('category_id', '')
    keyword = request.args.get('keyword', '')

    products = search_categories(cat_id, keyword) or []
    categories = get_all_categories() or []
    
    user_account = session.get(SESSION_AUTHO)
    if user_account:
        
        return render_template(
            "index.html", 
            products=products, 
            categories=categories,
            current_cat=cat_id,
            current_kw=keyword,
            auth=get_auth(user_account)
        )
    return render_template(
        "index.html", 
        products=products, 
        categories=categories,
        current_cat=cat_id,
        current_kw=keyword
    )
def product_detail_service(product_id):
    # 向 Models 索取這三樣資料
    # product, stock, extra_pics = models_shopping.get_product_detail(id)
    product = get_product_by_id(product_id)
    
    # 如果沒找到商品，顯示 404
    if not product:
        return "找不到該商品", 404
    
    stock = get_product_stock(product_id)
    extra_pics = get_product_pics(product_id)
    return render_template(
        "product.html",
        product=product,
        stock=stock,
        extra_pics=extra_pics
    )