import os
from dotenv import load_dotenv

# ________________________DATABASE______________________
load_dotenv()  # 讀取 .env 檔案，將其中的鍵值對載入為環境變數
DB_HOST     = os.getenv("DB_HOST")  # 從環境變數取得資料庫主機位址，覆蓋 settings 預設值
DB_PORT     = int(os.getenv("DB_PORT"))  # 從環境變數取得資料庫連線埠號，轉為整數
DB_USER     = os.getenv("DB_USER")  # 從環境變數取得資料庫登入帳號
DB_PASSWORD = os.getenv("DB_PASSWORD")  # 從環境變數取得資料庫登入密碼
DB_DATABASE = os.getenv("DB_DATABASE")  # 從環境變數取得資料庫名稱

# ________________________M.C.__________________________
MC_RCON_HOST = os.getenv("MC_RCON_HOST")
MC_RCON_PORT = int(os.getenv("MC_RCON_PORT"))
MC_RCON_PASSWORD = os.getenv("MC_RCON_PASSWORD")
# # ________________________POOL__________________________
# POOL_NAME = "pool"
# POOL_SIZE = 5
# ________________________BRANCH TABLES_________________
BRANCH_A_TABLE = "user"

BRANCH_B_PRODUCTS_TABLE         = "products"
BRANCH_B_PRODUCT_CATEGORY_TABLE = "product_category"
BRANCH_B_PRODUCT_PICS_TABLE     = "product_pics"
BRANCH_B_PRODUCT_STOCK_TABLE    = "product_stock"

BRANCH_C_CART_TABLE                  = "cart_items"
BRANCH_C_ORDER_TABLE                 = "orders"
BRANCH_C_ORDER_ITEMS_TABLE           = "order_items"
BRANCH_C_ACTIVE_TAG_TABLE            = "active_tag"
BRANCH_C_PENDING_DELIVERIES_TABLE    = "pending_deliveries"

BRANCH_D_MANAGE_LOG_TABLE       = "manage_log"
BRANCH_D_MEMBER_CARDS_TABLE      = "member_cards"

# ________________________EMAIL_________________________
MAIL_SERVER='smtp.gmail.com'
MAIL_PORT = 465
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_USE_TLS = False
MAIL_USE_SSL = True


CODE_EXPIRE_MINUTES = 5

# ________________________FLASK_________________________
APP_PORT = 7775 # FLASK啟用時所用的埠號 預設為8000 可以自行調整
SESSION_KEY = "MyShoppingAppProject" # 建立SESSION時使用的SESSION KEY
SESSION_AUTHO = "AUTHO" # 用於儲存使用者登入狀態的KEY 各分支會將以此作為判斷使用者是否登入用的依據(整合後才會用到)

# ________________________PROFILE PIC___________________
PROFILE_TEMP_FOLDER = os.path.join("static", "profile", "temp")
PROFILE_PIC_FOLDER = os.path.join("static", "profile")
PROFILE_TEMP_PATH = os.path.join(PROFILE_TEMP_FOLDER, "{}")
PROFILE_PIC_PATH = os.path.join(PROFILE_PIC_FOLDER, "{}")

# ________________________PORDUCT PIC___________________
PRODUCT_PIC_FOLDER = os.path.join("static", "uploads")
PRODUCT_PIC_PATH = os.path.join(PRODUCT_PIC_FOLDER, "{}")
# ________________________MANAGE________________________
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}