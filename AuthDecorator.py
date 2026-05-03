from settings import SESSION_AUTHO
from functools import wraps
from flask import request,session,render_template,flash,redirect,url_for
from utils import getVerifyToken
from models import getUser,updateUser

"""
在此設計方便各分支使用的防呆裝飾器
用於判斷使用者是否登入中 及 未登入
防止使用者亂輸入網址 進到一些可能會影響後端資料的網頁中 存取資料庫資料
是完整性中最重要的一環
"""

# 必須要登入中 才可進行的功能 皆可用此裝飾器做包裝
def loginRequired(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if SESSION_AUTHO in session:
            if session.get(SESSION_AUTHO) != "admin":
                return fun(*args,**kwargs)
            return render_template("manage.html")
        return render_template("login.html")
    return wrap

# 已登入的使用者 不可再進入註冊或登入頁面
def guestOnly(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if not SESSION_AUTHO in session:
            return fun(*args,**kwargs)
        return render_template("index.html")
    return wrap

# 只有admin管理員可以使用的功能 皆可用此裝飾器做包裝
def adminRequired(fun):
    @wraps(fun)
    def wrap(*args,**kwargs):
        if session.get(SESSION_AUTHO) == "admin":
            return fun(*args,**kwargs)
        return render_template("index.html")
    return wrap

def tokenRequired(refresh = False):
    def decorator(fun):
        @wraps(fun)
        def wrap(*args,**kwargs):
            token = kwargs.get("token")
            ori_token = getUser({"token":token},"token")
            if ori_token is None:
                return render_template("index.html")
            
            if refresh is True:
                new_token = getVerifyToken(32)
                updateUser({"token":new_token},{"token":ori_token})
                kwargs["token"] = new_token
            return fun(*args,**kwargs)
        return wrap
    return decorator
            