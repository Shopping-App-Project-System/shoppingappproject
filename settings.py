import os
# ________________________DATABASE______________________
HOST = "127.0.0.1"
PORT = 3307
USER = "root"
PASSWORD = "114321"
DATABASE = "project"

BRANCH_A_TABLE = "user"
BRANCH_B_TABLE              = "products"
BRANCH_C_CART_TABLE         = "cart_items"
BRANCH_C_ORDER_TABLE        = "orders"
BRANCH_C_ORDER_ITEMS_TABLE  = "order_items"

# ________________________FLASK_________________________
APP_PORT = 8000 # FLASK啟用時所用的埠號 預設為8000 可以自行調整
SESSION_KEY = "MyShoppingAppProject" # 建立SESSION時使用的SESSION KEY
SESSION_AUTHO = "AUTHO" # 用於儲存使用者登入狀態的KEY 各分支會將以此作為判斷使用者是否登入用的依據(整合後才會用到)

# ________________________PROFILE PIC___________________
PROFILE_TEMP_PATH = os.path.join("static","profile","temp","{}")
PROFILE_PIC_PATH = os.path.join("static","profile","{}")

"""
關於專案的設定 都可以於此做撰寫 用settings.VARIABLE的方式 來做使用
好處是 : 以便於收整 以及 後續維護
"""
