# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
import models_shopping
import settings
from utils import get_auth

# _______________________________________初始化___________________________________________
bp = Blueprint("index",__name__)
# ________________________________________API_____________________________________________ 
@bp.route("/")
def index():
    cat_id = request.args.get('category_id', '')
    keyword = request.args.get('keyword', '')

    products = models_shopping.search_categories(cat_id, keyword) or []
    categories = models_shopping.get_all_categories() or []
    
    user_account = session.get(settings.SESSION_AUTHO)
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