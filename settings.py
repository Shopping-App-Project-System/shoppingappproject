"""全域設定檔。

原則：
    1. 這裡只放「設定」——會隨部署環境改變的值，或整個專案共用的常數。
    2. 機密（密碼、API 金鑰）一律從 .env 讀取，絕不寫死在這個檔案裡。
    3. 純資料（例如商品對照表）放在 data/ 底下，不要塞進這裡。

新進成員請先複製 .env.example 成 .env 並填入自己的值。
"""

import os

from dotenv import load_dotenv

from data.mc_items import MC_PRODUCT_ITEMS  # noqa: F401  (相容既有 from settings import MC_PRODUCT_ITEMS)

load_dotenv()  # 讀取 .env 檔案，將其中的鍵值對載入為環境變數


def _env_int(key: str, default: int) -> int:
    """讀取整數型環境變數；沒設定或格式錯誤時回傳預設值。

    直接用 int(os.getenv(key)) 在 .env 不存在時會拋出語意不明的
    TypeError: int() argument must be...，讓新成員很難判斷是漏了 .env。
    """
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"環境變數 {key} 必須是整數，目前的值是：{raw!r}") from None


def _env_str(key: str, default: str) -> str:
    """讀取字串型環境變數；沒設定或留空時回傳預設值。

    os.getenv(key, default) 只在「變數完全不存在」時才回傳 default。
    .env 裡寫成 KEY=（有這一行但沒填值）時，拿到的是空字串 ''，
    預設值不會生效——這正是綠界回報「10200074 找不到加密金鑰」的原因：
    MerchantID 與 HashKey 都被送成空字串。

    只用於「空字串不是合理設定值」的項目；DB_PASSWORD、MC_RCON_PASSWORD
    這類可以合法為空的，維持直接讀取。
    """
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


# ─────────────────────────── 資料庫 ───────────────────────────
DB_HOST     = _env_str("DB_HOST", "127.0.0.1")   # 資料庫主機位址
DB_PORT     = _env_int("DB_PORT", 3306)           # 連線埠（MySQL 8.0 預設 3306 / 本機 MariaDB 為 3307）
DB_USER     = _env_str("DB_USER", "root")        # 登入帳號
DB_PASSWORD = os.getenv("DB_PASSWORD", "")        # 登入密碼
DB_DATABASE = _env_str("DB_DATABASE", "shoppingapp")  # 資料庫名稱

# ─────────────────────── 資料表名稱對照 ───────────────────────
# 命名沿用開發期的分支代號：A=帳號 B=商品 C=購物/訂單 D=後台日誌
BRANCH_A_TABLE                    = "user"

BRANCH_B_PRODUCTS_TABLE           = "products"
BRANCH_B_PRODUCT_PICS_TABLE       = "product_pics"
BRANCH_B_PRODUCT_STOCK_TABLE      = "product_stock"

BRANCH_C_CART_TABLE               = "cart_items"
BRANCH_C_ORDER_TABLE              = "orders"
BRANCH_C_ORDER_ITEMS_TABLE        = "order_items"
BRANCH_C_ACTIVE_TAG_TABLE         = "active_tag"
BRANCH_C_PENDING_DELIVERIES_TABLE = "pending_deliveries"

BRANCH_D_MANAGE_LOG_TABLE         = "manage_log"

# ──────────────────────── Flask / Session ────────────────────────
APP_PORT      = _env_int("APP_PORT", 7775)  # Flask 啟用時所用的埠號
SESSION_KEY   = _env_str("SESSION_KEY", "MyShoppingAppProject")  # 建立 SESSION 時使用的 KEY
SESSION_AUTHO = "AUTHO"                     # 儲存使用者登入狀態的 session key

SESSION_EXPIRE_HOURS = 3  # 登入狀態有效時數
CODE_EXPIRE_MINUTES  = 5  # 信箱驗證碼有效分鐘數

# ───────────────────────────── 郵件 ─────────────────────────────
MAIL_SERVER   = "smtp.gmail.com"
MAIL_PORT     = 465
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_USE_TLS  = False
MAIL_USE_SSL  = True

# ────────────────────── Minecraft 伺服器 RCON ──────────────────────
MC_RCON_HOST     = _env_str("MC_RCON_HOST", "127.0.0.1")
MC_RCON_PORT     = _env_int("MC_RCON_PORT", 25575)
MC_RCON_PASSWORD = os.getenv("MC_RCON_PASSWORD", "")

# ───────────────────── Cloudinary 圖片託管 ─────────────────────
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# ─────────────────────────── 圖片規則 ───────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
PROFILE_FOLDER     = "profile"
PRODUCT_FOLDER     = "product"

PROFILE_DEFAULT_PATH = f"https://res.cloudinary.com/dca1ag2yt/image/upload/v1779814173/static/{PROFILE_FOLDER}/default_profile.png"
PRODUCT_DEFAULT_PATH = f"https://res.cloudinary.com/dca1ag2yt/image/upload/v1779760174/static/{PRODUCT_FOLDER}/default_product.png"

# ────────────────────────── ECPay 綠界金流 ──────────────────────────
# 預設值為綠界官方文件公開的測試金鑰，任何人都能直接用來跑測試流程。
# 要換成自己的測試商店，把這三個值寫進 .env 即可。
ECPAY_MERCHANT_ID = _env_str("ECPAY_MERCHANT_ID", "3002607")
ECPAY_HASH_KEY    = _env_str("ECPAY_HASH_KEY", "pwFHCqoQZGmho4w6")
ECPAY_HASH_IV     = _env_str("ECPAY_HASH_IV", "EkRm7iFT261dpevs")

# 綠界 AIO 結帳端點
#   測試環境：https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
#   正式環境：https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5
ECPAY_AIO_URL = _env_str("ECPAY_AIO_URL", "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5")

# ngrok 公開網址：綠界的 server-to-server callback 需要它才打得到本機。
# 每次重開 ngrok 網址都會變，記得同步更新 .env。
NGROK_URL = _env_str("NGROK_URL", f"http://localhost:{APP_PORT}")

# 本機網址：綠界讓「使用者瀏覽器」跳回的位址。
# 必須用 localhost 而非 ngrok，否則跨 domain 會拿不到 session cookie。
LOCAL_URL = f"http://localhost:{APP_PORT}"
