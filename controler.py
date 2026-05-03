# __________________________________________內部模組_____________________________________
from flask import Flask

# _______________________________________自定義模組_______________________________________
from settings import SESSION_KEY,MAIL_SERVER,MAIL_PORT,MAIL_USERNAME,MAIL_PASSWORD,MAIL_USE_TLS,MAIL_USE_SSL,APP_PORT
from extension import init_mail
# _______________________________________blue print______________________________________
from modules.Authentication.Authentication_routers import bp as Authentication_bp
from modules.Product.Product_routers import bp as Product_bp
from modules.Shopping.Shopping_routers import bp as Shopping_bp
from modules.Management.Management_routers import bp as Management_bp

# _______________________________________初始化___________________________________________
app = Flask(__name__)
app.secret_key = SESSION_KEY

app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL

# ________________________________________routors_________________________________________
app.register_blueprint(Authentication_bp)
app.register_blueprint(Product_bp)
app.register_blueprint(Shopping_bp)
app.register_blueprint(Management_bp)

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False,port=APP_PORT)
    init_mail(app)
