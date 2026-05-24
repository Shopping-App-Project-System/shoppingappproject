# __________________________________________內部模組_____________________________________
from flask import request,render_template
from werkzeug.utils import secure_filename
from secrets import token_urlsafe
from random import randint
from functools import wraps
from shutil import move,copy
import os
import re
import inspect
from datetime import datetime
# _______________________________________自定義模組_______________________________________
from models import getUser
from settings import ALLOWED_EXTENSIONS,APP_PORT,CODE_EXPIRE_MINUTES
import warnings
# _______________________________________初始化___________________________________________

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

# ── 路徑處理 ──────────────────────────────────────────────────────────────────

def normalize_path(path):
    if path:
        path = path.replace("\\", "/")
        if not path.startswith("/"):
            path = "/" + path
        return path
    return None

def copy_image(src, dst):
    src = src.lstrip("/")
    dst = dst.lstrip("/")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    copy(src, dst)
    return "/" + dst.replace("\\", "/")

def move_image(src, dst):
    src = src.lstrip("/")
    dst = dst.lstrip("/")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    move(src, dst)
    return "/" + dst.replace("\\", "/")

def del_imgae(src):
    src = src.lstrip("/")
    if os.path.exists(src):
        os.remove(src)

def save_image(file, folder, filename=None):
    if file and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            if filename is None:
                filename = secure_filename(file.filename)
            else:
                filename = f"{filename}.{ext}"
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, filename))
            path = os.path.join(folder, filename)
            return "/" + path.replace("\\", "/")
    return None

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_auth(user_account):
    return {
        "logged_in"  : True,
        "account"    : user_account,
        "profile_pic": normalize_path(getUser({"user_account": user_account}, "pic_path"))
    }
