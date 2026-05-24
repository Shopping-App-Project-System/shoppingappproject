# __________________________________________內部模組_____________________________________
from flask import render_template,session

# _______________________________________自定義模組_______________________________________
from models import search_categories,get_product_by_id,get_product_stock,get_product_pics
from settings import SESSION_AUTHO,MC_PRODUCT_ITEMS
from utils import get_auth,requestParsor

# _______________________________________初始化___________________________________________


# ________________________________________services_____________________________________________
@requestParsor
def index_service(category="",keyword=""):
    products = search_categories(category, keyword) or []
    categories = list(MC_PRODUCT_ITEMS.keys())
    
    user_account = session.get(SESSION_AUTHO)
    if user_account:
        
        return render_template(
            "index.html", 
            products=products, 
            categories=categories,
            current_cat=category,
            current_kw=keyword,
            auth=get_auth(user_account)
        )
    return render_template(
        "index.html", 
        products=products, 
        categories=categories,
        current_cat=category,
        current_kw=keyword
    )

def product_detail_service(product_id):
    # 向 Models 索取這三樣資料
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
'''
    if profile_pic is None or profile_pic.filename == "":
        user_filename = account + ".png"
        ori_pic_path = PROFILE_TEMP_PATH.format("default.png")
        user_pic_path = PROFILE_TEMP_PATH.format(user_filename)
        user_pic_path = copy_image(ori_pic_path, user_pic_path)
    else: 
        user_pic_path = save_image(profile_pic, PROFILE_TEMP_FOLDER, filename=name)
'''