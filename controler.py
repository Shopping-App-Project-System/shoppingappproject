# __________________________________________內部模組_____________________________________
from flask import Flask

# _______________________________________自定義模組_______________________________________
from settings import SESSION_KEY,MAIL_SERVER,MAIL_PORT,MAIL_USERNAME,MAIL_PASSWORD,MAIL_USE_TLS,MAIL_USE_SSL,APP_PORT
from extension import init_mail

# _______________________________________初始化___________________________________________
app = Flask(__name__)
app.secret_key = SESSION_KEY

# ── Session cookie 行為調整 ──
# 預設情況下，Flask 會在「每個請求」結束時把 session 寫回 cookie，
# 即使 session 沒有任何變動。這在大部分情境下是安全的，但在綠界這類
# cross-site POST callback 場景會出問題：
#   - 綠界 POST 跳回時，Chrome 因 SameSite=Lax 不送 session cookie
#   - Flask 收到請求，session 是空的（因為沒帶 cookie）
#   - 結束時 Flask 把「空 session」寫回 cookie，覆蓋使用者原本的登入狀態
#   - 使用者整個被登出
#
# 設為 False 後，Flask 只在 session 真的「有變動」時才寫回 cookie，
# 綠界回跳這類「只讀不改」的請求就不會影響使用者登入狀態。
app.config['SESSION_REFRESH_EACH_REQUEST'] = False

app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
init_mail(app)

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
