# __________________________________________內部模組_____________________________________
from flask import Flask

# _______________________________________自定義模組_______________________________________
from settings import (SESSION_KEY, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD,
                      MAIL_USE_TLS, MAIL_USE_SSL, APP_PORT,
                      PRODUCT_DEFAULT_PATH, PROFILE_DEFAULT_PATH)
from extension import init_mail

# _______________________________________初始化___________________________________________
app = Flask(__name__)
app.secret_key = SESSION_KEY

app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
init_mail(app)


# _______________________________________樣板共用變數______________________________________
@app.context_processor
def inject_default_images():
    """讓所有樣板都能取得預設圖網址。

    原本 index.html 與 cart.html 各自寫死 '/static/default.png'，
    但該檔案並不存在，商品沒有圖片時會出現破圖；
    settings.py 早就備有 PRODUCT_DEFAULT_PATH / PROFILE_DEFAULT_PATH，
    Python 端也在用，只有樣板端沒接上。這裡統一注入。
    """
    return {
        "PRODUCT_DEFAULT_PATH": PRODUCT_DEFAULT_PATH,
        "PROFILE_DEFAULT_PATH": PROFILE_DEFAULT_PATH,
    }


# _______________________________________blue print______________________________________
from modules.Authentication.Authentication_routers import bp as Authentication_bp
from modules.Product.Product_routers import bp as Product_bp
from modules.Shopping.Shopping_routers import bp as Shopping_bp
from modules.Management.Management_routers import bp as Management_bp

# ________________________________________routors_________________________________________
app.register_blueprint(Authentication_bp)
app.register_blueprint(Product_bp)
app.register_blueprint(Shopping_bp)
app.register_blueprint(Management_bp)

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False,port=APP_PORT)