# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,make_response,Flask,url_for,flash,Blueprint

# _______________________________________自定義模組_______________________________________
from models_shopping import add_product,add_log
from AuthDecorator import adminRequired
from settings import UPLOAD_FOLDER,SESSION_AUTHO
from utils import save_image
# _______________________________________初始化___________________________________________
bp = Blueprint("manage_add",__name__)

# ________________________________________API_____________________________________________
@bp.route("/manage/add", methods=["POST"])
@adminRequired
def manage_add():
    name         = request.form.get("name")
    price        = request.form.get("price")
    description  = request.form.get("description")
    file         = request.files.get("image")
    img_filename = save_image(file, UPLOAD_FOLDER)
    add_product(name, price, description, img_filename)
    add_log(session.get(SESSION_AUTHO), "上架", None, name)
    flash("商品已上架", "success")
    return redirect(url_for("manage"))