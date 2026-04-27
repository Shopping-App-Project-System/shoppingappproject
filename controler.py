# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash
# from flask_mail import Mail, Message




# _______________________________________自定義模組_______________________________________
import settings
from models import Models
# from fool_proof import *


# _______________________________________初始化___________________________________________
app = Flask(__name__)
model = Models()



# ________________________________________API_____________________________________________

# ____templates file names____
# index.html
# register.html
# login.html
# member.html
# checkout.html
# cart.html
# manage.html

@app.route("/")

#__________商品搜尋列__________
def search_categories():
    cat_id = request.args.get('category_id', '')
    keyword = request.args.get('keyword', '')

    products = model.search_categories(cat_id, keyword)
    categories = model.get_all_categories()

    return render_template(
        "index.html", 
        products=products, 
        categories=categories,
        current_cat=cat_id,
        current_kw=keyword
    )

#__________商品詳細頁__________
@app.route("/product/<int:id>")
def product_detail(id):
    # 向 Models 索取這三樣資料
    product, stock, extra_pics = model.get_product_detail(id)

    # 如果沒找到商品，顯示 404
    if not product:
        return "找不到該商品", 404

    return render_template(
        "product.html",
        product=product,
        stock=stock,
        extra_pics=extra_pics
    )
    
if __name__ == "__main__":
    """先於settings.py中設定APP_PORT"""
    app.run(debug=True,use_reloader=False,port=settings.APP_PORT)
