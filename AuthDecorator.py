import settings
import re
from functools import wraps
from flask import request, session, render_template, flash, redirect, url_for
from utils import getVerifyToken

"""
在此設計方便各分支使用的防呆裝飾器
用於判斷使用者是否登入中 及 未登入
防止使用者亂輸入網址 進到一些可能會影響後端資料的網頁中 存取資料庫資料
是完整性中最重要的一環
"""
# ── 登入驗證 ──────────────────────────────────────────────────────────────────

# 必須要登入中 才可進行的功能 皆可用此裝飾器做包裝
def loginRequired(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if settings.SESSION_AUTHO in session:
            return fun(*args,**kwargs)
        return redirect(url_for("login"))
    return wrap

# 已登入的使用者 不可再進入註冊或登入頁面
def guestOnly(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if not settings.SESSION_AUTHO in session:
            return fun(*args,**kwargs)
        return render_template("index.html")
    return wrap

# 只有admin管理員可以使用的功能 皆可用此裝飾器做包裝
def adminRequired(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if session.get(settings.SESSION_AUTHO) == "admin":
            return fun(*args,**kwargs)
        return render_template("index.html")
    return wrap

def tokenRequired(model,refresh = False):
    def decorator(fun):
        @wraps(fun)
        def wrap(*args,**kwargs):
            token = kwargs.get("token")
            ori_token = model.getUser({"token":token},"token")
            if ori_token is None:
                return render_template("index.html")
            
            if refresh is True:
                new_token = getVerifyToken(32)
                model.updateUser({"token":new_token},{"token":ori_token})
                kwargs["token"] = new_token
            return fun(*args,**kwargs)
        return wrap
    return decorator


# ── 格式驗證（正規表示式）────────────────────────────────────────────────────────

def validateEmail(email):
    # 信箱格式：第一個英文(不分大小寫)，英文或數字，@，英文或數字，.，com
    pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]*@[a-zA-Z0-9]+\.com$')
    return pattern.search(email)


def validatePhone(phone):
    # 台灣手機格式：09 開頭，後接 8 位數字，共 10 碼
    pattern = re.compile(r'^09\d{8}$')
    return pattern.search(phone)


def validateCreditCard(card):
    # 信用卡格式：16 位數字，每 4 碼可用 - 或空格分隔（可省略）
    # \d{4} 對應每組 4 碼，[-\s]? 對應可有可無的分隔符號
    pattern = re.compile(r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$')
    return pattern.search(card)
