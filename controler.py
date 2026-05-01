# __________________________________________內部模組_____________________________________
from flask import Flask

# _______________________________________自定義模組_______________________________________
from settings import SESSION_KEY,MAIL_SERVER,MAIL_PORT,MAIL_USERNAME,MAIL_PASSWORD,MAIL_USE_TLS,MAIL_USE_SSL,APP_PORT
from extension import init_mail

from modules.index_module import bp as index_bp
from modules.register_module import bp as register_bp
from modules.verify_register_module import bp as verify_register_bp
from modules.login_module import bp as login_bp
from modules.forgot_password_module import bp as forgot_password_bp
from modules.reset_password_module import bp as reset_password_bp
from modules.forgot_account_module import bp as forgot_account_bp
from modules.forgot_verify_account_module import bp as forgot_verify_account_bp
from modules.logout_module import bp as logout_bp
from modules.product_detail_module import bp as product_detail_bp
from modules.member_module import bp as member_bp
from modules.member_edit_module import bp as member_edit_bp
from modules.cart_module import bp as cart_bp
from modules.cart_add_module import bp as cart_add_bp
from modules.cart_remove_module import bp as cart_remove_bp
from modules.checkout_module import bp as checkout_bp
from modules.order_cancel_module import bp as order_cancel_bp
from modules.manage_module import bp as manage_bp
from modules.manage_add_module import bp as manage_add_bp
from modules.manage_remove_module import bp as manage_remove_bp
from modules.manage_clear_moduel import bp as manage_clear_bp
from modules.manage_restore_module import bp as manage_restore_bp
from modules.manage_restock_mdule import bp as manage_restock_bp

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

# ________________________________________API_____________________________________________
app.register_blueprint(index_bp)
app.register_blueprint(register_bp)
app.register_blueprint(verify_register_bp)
app.register_blueprint(login_bp)
app.register_blueprint(forgot_password_bp)
app.register_blueprint(reset_password_bp)
app.register_blueprint(forgot_account_bp)
app.register_blueprint(forgot_verify_account_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(product_detail_bp)
app.register_blueprint(member_bp)
app.register_blueprint(member_edit_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(cart_add_bp)
app.register_blueprint(cart_remove_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(order_cancel_bp)
app.register_blueprint(manage_bp)
app.register_blueprint(manage_add_bp)
app.register_blueprint(manage_remove_bp)
app.register_blueprint(manage_clear_bp)
app.register_blueprint(manage_restore_bp)
app.register_blueprint(manage_restock_bp)

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False,port=APP_PORT)
