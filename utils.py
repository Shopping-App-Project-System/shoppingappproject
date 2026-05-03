# __________________________________________內部模組_____________________________________
from flask import request
from werkzeug.utils import secure_filename
from secrets import token_urlsafe
from random import randint
from functools import wraps
from shutil import move,copy
import os
import re

# _______________________________________自定義模組_______________________________________
from models import getUser
from settings import ALLOWED_EXTENSIONS

# _______________________________________初始化___________________________________________


# ________________________________________API_____________________________________________
def parse_request(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        kwargs.update(request.args)
        kwargs.update(request.form)
        kwargs.update(request.files)
        return fun(*args, **kwargs)
    return wrap
        
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

def checkUserInput(datas, **msgs):
    # 逐一確認必填欄位，回傳缺少欄位的顯示名稱（以「、」串接），全部填寫則回傳空字串
    missing = []
    for key, msg in msgs.items():
        if not datas[key]:
            missing.append(msg)

    return "、".join(missing)

# ── 驗證碼與 Token ────────────────────────────────────────────────────────────

def getRandomVerifyCode(digits):return "".join(list(str(randint(0,9)) for _ in range(digits)))
# 產生指定位數的純數字驗證碼，例如 getRandomVerifyCode(6) → '473829'

def getVerifyToken(digits):return token_urlsafe(digits)    
# 產生指定長度的 URL-safe 隨機 token，用於驗證信連結

def validateEmail(email):
    # 信箱格式：第一個英文(不分大小寫)，英文或數字，@，英文或數字，.，com
    pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*@[a-zA-Z0-9]+\.com$')
    return bool(pattern.search(email))


def validateMobile(phone):
    # 台灣手機格式：09 開頭，後接 8 位數字，共 10 碼
    pattern = re.compile(r'^09\d{8}$')
    return bool(pattern.search(phone))


def validateCreditCard(card):
    # 信用卡格式：16 位數字，每 4 碼可用 - 或空格分隔（可省略）
    # \d{4} 對應每組 4 碼，[-\s]? 對應可有可無的分隔符號
    pattern = re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$')
    return bool(pattern.search(card))
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
    if src:
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
    