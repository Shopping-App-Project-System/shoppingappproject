from secrets import token_urlsafe
from random import randint
import settings
import os

# ── 表單解析 ──────────────────────────────────────────────────────────────────

def getResponseForm(datas,*selections):
    # 不傳 selections：回傳所有欄位值；傳單一欄位：直接回傳值；傳多個：回傳 tuple
    if not len(selections):
        return tuple(datas[selection] for selection in list(datas.keys()))
    else:
        datas = tuple(datas[selection] for selection in selections)
        if len(selections)  == 1:
            return datas[0]
        return datas

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
