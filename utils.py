# __________________________________________內部模組_____________________________________
from flask import request,redirect,url_for,session
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
from settings import ALLOWED_EXTENSIONS,SESSION_AUTHO
import warnings
# _______________________________________初始化___________________________________________

# ___________________________________service routine_____________________________________
def requestParsor(fun):
    sig = inspect.signature(fun)
    @wraps(fun)
    def wrap(*args, **kwargs):
        result = {}
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
# _______________________________________全局例外處理______________________________________
# def exceptionCatcher(msg):
#     def decorator(fun):
#         @wraps(fun)
#         def wrap(*args,**kwargs):
            
#             try:
#                 return fun(*args,**kwargs)
#             except Exception as e:
#                 session['error'] = {
#                     'msg': str(msg),
#                     'exception': str(e),
#                     'route': request.path,
#                     'method': request.method,
#                     'dt': str(datetime.now()),
#                     'account': session.get(SESSION_AUTHO)
#                 }
#                 return redirect(url_for('error'))
#         return wrap
#     return decorator

    
# ________________________________________API_____________________________________________
        
def getResponseForm(datas, *selections, default=None):
    # 不傳 selections：回傳所有欄位值；傳單一欄位：直接回傳值；傳多個：回傳 tuple
    if not len(selections):
        return tuple(datas.get(key, default) for key in datas.keys())
    else:
        result = tuple(datas.get(selection, default) for selection in selections)
        if len(selections) == 1:
            return result[0]
        return result

def getResponseArgs(datas, *selections, default=None):
    if not len(selections):
        return tuple(datas)
    else:
        result = tuple(
            datas[i] if i < len(datas) else default
            for i in selections
        )
        if len(selections) == 1:
            return result[0]
        return result

def getResponseFile(files, *selections):
    # 從 request.files 取出指定的 FileStorage 物件，邏輯同 getResponseForm
    if not selections:
        return tuple(files.get(key) for key in files.keys())
    
    datas = tuple(files.get(selection) for selection in selections)
    
    if len(selections) == 1:
        return datas[0]
    
    return datas

def checkUserInput(*args):
    missing = [msg for msg, value in args if not value]
    return "、".join(missing)

# ── 驗證碼與 Token ────────────────────────────────────────────────────────────

def getRandomVerifyCode(digits):return "".join(list(str(randint(0,9)) for _ in range(digits)))
# 產生指定位數的純數字驗證碼，例如 getRandomVerifyCode(6) → '473829'

def getVerifyToken(digits):return token_urlsafe(digits)    
# 產生指定長度的 URL-safe 隨機 token，用於驗證信連結

def validateEmail(email):
    # 信箱格式：第一個英文(不分大小寫)，英文或數字，@，英文或數字，.，com
    pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*@[a-zA-Z0-9]+\.com$')
    return pattern.search(email)


def validateMobile(mobile):
    # 台灣手機格式：09 開頭，後接 8 位數字，共 10 碼
    pattern = re.compile(r'^09\d{8}$')
    return pattern.search(mobile)


def validateCreditCard(card):
    # 信用卡格式：16 位數字，每 4 碼可用 - 或空格分隔（可省略）
    # \d{4} 對應每組 4 碼，[-\s]? 對應可有可無的分隔符號
    pattern = re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$')
    return pattern.search(card)

def validateMCUserAccount(user_account):
    pattern = re.compile(r"^[a-zA-Z0-9_]{1,16}$")
    return pattern.search(user_account)
# __________________________________________________________________________________
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
# _______________________Auth________________
def get_auth(user_account):
    return{
        "logged_in"  : True,
        "account"    : user_account,
        "profile_pic": normalize_path(getUser({"user_account": user_account}, "pic_path"))
    }
    