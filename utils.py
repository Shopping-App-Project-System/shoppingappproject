# __________________________________________內部模組_____________________________________
from flask import request,render_template,session,flash,redirect,url_for
from werkzeug.utils import secure_filename
from secrets import token_urlsafe
from random import randint
from functools import wraps
from shutil import move,copy
import os
import re
import inspect
from datetime import datetime,timedelta

# _______________________________________自定義模組_______________________________________
from models import getUser,updateUser
from settings import ALLOWED_EXTENSIONS,APP_PORT,CODE_EXPIRE_MINUTES,SESSION_EXPIRE_HOURS,SESSION_AUTHO
import warnings
# _______________________________________商品___________________________________________


# ___________________________________service routine_____________________________________
def requestParsor(fun):
    sig = inspect.signature(fun)
    @wraps(fun)
    def wrap(*args, **kwargs):
        result = {}
        result.update(request.view_args)
        result.update(request.form)
        result.update(request.args)
        result.update(request.files)
        for name, param in sig.parameters.items():
            if name not in result and name not in kwargs:
                if param.default is inspect.Parameter.empty:
                    result[name] = None
                else:
                    result[name] = param.default
        extra_keys = [k for k in result if k not in sig.parameters.keys()]
        if extra_keys:
            warnings.warn(f"[requestParsor] {fun.__name__}() 收到未定義的參數，已忽略：{extra_keys}")
        result = {k: v for k, v in result.items() if k in sig.parameters.keys()}
        return fun(*args, **kwargs, **result)
    return wrap

def checkUserInput(*args):
    missing = [msg for msg, value in args if not value]
    return "、".join(missing)

def _is_expired(expires_at):
    if expires_at is None:
        return True
    return datetime.now() > expires_at

def _validate_session(account):
    """
    驗證 session token 是否有效，並刷新過期時間。
    回傳 True 表示有效，False 表示無效（需強制登出）
    """
    session_token = session.get("session_token")
    if not session_token:
        return False

    user = getUser({"user_account": account}, "session_token", "session_expires_at")
    if not user:
        return False

    # 比對 token
    if user["session_token"] != session_token:
        return False

    # 檢查是否過期
    if user["session_expires_at"] is None or datetime.now() > user["session_expires_at"]:
        return False

    # 刷新過期時間 (sliding session)
    new_expires_at = datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)
    updateUser({"session_expires_at": new_expires_at}, {"user_account": account})

    return True

def _force_logout():
    """強制清除 session"""
    session.pop(SESSION_AUTHO, None)
    session.pop("session_token", None)
    flash("登入已過期或帳號在其他裝置登入，請重新登入", "error")
    return redirect(url_for("A.login"))


# ── Minecraft 風格驗證信 ───────────────────────────────────────────────────────

def _mc_mail_html(account, code, token, route, title="帳號驗證", subtitle="請完成驗證以加入伺服器"):
    return render_template(
        "mail_verify.html",
        account=account,
        code=str(code),
        route=route,
        title=title,
        subtitle=subtitle,
        port=APP_PORT,
        expire_minutes=CODE_EXPIRE_MINUTES
    )

# ── 驗證碼與 Token ────────────────────────────────────────────────────────────

def getRandomVerifyCode(digits):
    return "".join(list(str(randint(0,9)) for _ in range(digits)))

def getVerifyToken(digits):
    return token_urlsafe(digits)

def validateEmail(email):
    pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*@[a-zA-Z0-9]+\.com$')
    return pattern.search(email)

def validateCreditCard(card):
    pattern = re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$')
    return pattern.search(card)

def validateMCUserAccount(user_account):
    pattern = re.compile(r"^[a-zA-Z0-9_]{1,16}$")
    return pattern.search(user_account)

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_auth(user_account):
    return {
        "logged_in"  : True,
        "account"    : user_account,
        "profile_pic": getUser({"user_account": user_account}, "pic_path")
    }
