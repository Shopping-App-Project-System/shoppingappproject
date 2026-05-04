# __________________________________________內部模組_____________________________________
from flask import Blueprint

# _______________________________________自定義模組_______________________________________
from AuthDecorator import loginRequired,guestOnly,tokenRequired
from .Authentication_services import forgot_account_service,forgot_password_service,forgot_verify_account_service,reset_verify_password_service,login_service,logout_service,register_service,reset_password_service,verify_register_service
# _______________________________________初始化___________________________________________
bp = Blueprint("A",__name__)

# ________________________________________API_____________________________________________
@bp.route("/login/find/account",methods = ["POST","GET"])
@guestOnly
def forgot_account():return forgot_account_service()

# 忘記密碼：GET 顯示表單，POST 驗證帳號與信箱後發送重設密碼驗證信
@bp.route("/login/find/password",methods = ["POST","GET"])
@guestOnly
def forgot_password():return forgot_password_service()

# 找回帳號驗證碼確認：POST 比對驗證碼，成功後以 flash 顯示帳號給使用者
@bp.route("/login/find/account/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def forgot_verify_account(token):return forgot_verify_account_service(token)

# 重設密碼驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後顯示重設密碼頁
@bp.route("/login/find/password/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def reset_verify_password(token):return reset_verify_password_service(token)


@bp.route("/login",methods = ["POST","GET"])
@guestOnly
def login():return login_service()


# 登出：清除 session 中的登入資訊並導回首頁
@bp.route("/logout")
@loginRequired
def logout():return logout_service()


# 註冊：GET 顯示表單，POST 驗證輸入、建立帳號、複製預設大頭貼、發送驗證信
@bp.route("/register",methods = ["POST","GET"])
@guestOnly
def register():return register_service()


# 重設密碼：POST 驗證新舊密碼不同且兩次輸入一致後更新密碼
@bp.route("/login/reset/password/<token>",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def reset_password(token):return reset_password_service(token)


# 信箱驗證碼確認：GET 顯示輸入頁，POST 比對驗證碼，成功後將大頭貼移至正式路徑並啟用帳號
@bp.route("/register/email/<token>/verify/code",methods=["POST","GET"])
@guestOnly
@tokenRequired(refresh = True)
def verify_register(token):return verify_register_service(token)