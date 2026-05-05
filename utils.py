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

# _______________________________________初始化___________________________________________

# ___________________________________service routine_____________________________________
def requestParsor(fun):
    @wraps(fun)              # 保留被裝飾函式的原始資訊
    def wrap(*args):         # *args 接收 Flask 傳入的位置參數（如路徑參數）
        result = {}                          # 建立空字典收集所有請求參數
        result.update(request.form)          # 塞入 POST 表單參數
        result.update(request.args)          # 塞入 GET query string 參數
        result.update(request.files)         # 塞入上傳的檔案參數
        
        sig = inspect.signature(fun)         # 讀取被裝飾函式的參數簽名
        for name, param in sig.parameters.items():  # 逐一遍歷函式需要的參數
            if name not in result:           # 如果這個參數在 request 裡沒有對應的值
                if param.default is inspect.Parameter.empty:  # 判斷這個參數有沒有預設值
                    result[name] = None      # 沒有預設值 → 補 None 避免報錯
                else:
                    result[name] = param.default  # 有預設值 → 用函式定義的預設值
        return fun(*args, **result)  # *args 保留位置參數，**result 展開所有收集到的參數
    return wrap               # 回傳包裝後的函式


"""
========================================
Parse 裝飾器使用說明
========================================

功能：
    自動從 request 中取出參數（GET / POST / FILES）
    並依照被裝飾函式的參數簽名，自動補齊缺少的參數。
    同時保留 Flask 原本的位置參數傳遞方式（*args）。

使用方式：
    @app.route('/example', methods=['GET', 'POST'])
    @Parse
    def example(keyword, cat_id, image=None):
        ...

參數處理規則：
    1. request 有傳對應名稱的值    → 直接使用該值
    2. request 沒傳，但函式有預設值 → 使用函式定義的預設值
    3. request 沒傳，函式也沒預設值 → 自動補 None

注意事項：
    - 前後端的參數名稱必須一致，名稱對不上會拿到 None
    - GET 和 POST 不要使用相同的參數名稱，避免互相覆蓋
    - 檔案上傳參數（request.files）也會自動處理
    - *args 會保留 Flask 傳入的位置參數，確保 Flask 原本的行為不受影響

範例：
    # 前端 GET 請求：/search?keyword=apple&cat_id=1
    @app.route('/search')
    @Parse
    def search(keyword, cat_id):
        print(keyword)  # 'apple'
        print(cat_id)   # '1'

    # 前端 POST 請求：product_id=123, name=手機
    @app.route('/add', methods=['POST'])
    @Parse
    def add(product_id, name, description=None):
        print(product_id)   # '123'
        print(name)         # '手機'
        print(description)  # None（沒傳但有預設值）

    # 選填參數沒傳也沒預設值
    @app.route('/test')
    @Parse
    def test(keyword, optional):
        print(keyword)   # request 有傳 → 正常取值
        print(optional)  # request 沒傳 → None
========================================
"""
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
    