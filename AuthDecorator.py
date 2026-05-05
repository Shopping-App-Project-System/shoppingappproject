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

# ── 身份驗證：未登入才能進（登入頁、註冊頁）────────────────────────────────
def guestOnly(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        if SESSION_AUTHO not in session:
            return fun(*args, **kwargs)
        return render_template("B.index")
    return wrap

# ── 角色控制：一般使用者才能進（購物車、訂單...）──────────────────────────
def userRequired(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        if SESSION_AUTHO not in session:
            return redirect(url_for("A.login"))
        if session.get(SESSION_AUTHO) != "admin":
            return fun(*args, **kwargs)
        return redirect(url_for("D.manage"))
    return wrap

# ── 角色控制：管理員才能進（後台管理...）──────────────────────────────────
def adminRequired(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        if SESSION_AUTHO not in session:
            return redirect(url_for("A.login"))
        if session.get(SESSION_AUTHO) == "admin":
            return fun(*args, **kwargs)
        return redirect(url_for("B.index"))
    return wrap

# ── 擋掉 admin，其他人都能進 ──────────────────────────
def blockAdmin(fun):
    @wraps(fun)
    def wrap(*args, **kwargs):
        if session.get(SESSION_AUTHO) == "admin":
            return redirect(url_for("D.manage"))  # admin導去管理頁
        return fun(*args, **kwargs)  # 未登入或一般使用者都放行
    return wrap

# ── Token 驗證：特殊功能驗證（重設密碼...）────────────────────────────────
def tokenRequired(refresh=False):
    def decorator(fun):
        @wraps(fun)
        def wrap(*args, **kwargs):
            token = kwargs.get("token")
            ori_token = getUser({"token": token}, "token")
            if ori_token is None:
                return redirect(url_for("B.index"))
            if refresh is True:
                new_token = getVerifyToken(32)
                updateUser({"token": new_token}, {"token": ori_token})
                kwargs["token"] = new_token
                request.view_args["token"] = new_token  # ← 更新給 requestParsor 用
            return fun(*args, **kwargs)
        return wrap
    return decorator