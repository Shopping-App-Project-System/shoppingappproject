"""
==========================================================
  綠界 ECPay 全方位金流串接輔助模組
==========================================================

【負責範圍】
  - CheckMacValue 簽章計算（SHA256）
  - 組綠界 AIO 全方位金流的送出參數
  - 驗證綠界回傳的 callback 簽章

【為什麼需要 CheckMacValue】
  綠界用這個值防止資料被竄改。簽章規則：
  1. 把所有參數依參數名稱 A→Z 排序
  2. 前面加 HashKey=xxx&、後面加 &HashIV=xxx
  3. 整串做 URL encode（用綠界規定的 .NET 風格）
  4. 全部轉小寫
  5. 做 SHA256
  6. 結果轉大寫

  錯一步整個對不上，所以這支函式不要亂改。

【公開測試金鑰】
  綠界官方文件公開提供的測試特店資料：
    MerchantID = 3002607
    HashKey    = pwFHCqoQZGmho4w6
    HashIV     = EkRm7iFT261dpevs
  把它們放在 .env 即可使用。
==========================================================
"""
import hashlib
from urllib.parse import quote_plus
from datetime import datetime
# ════════════════════════════════════════════════════════════════
#   綠界 API 端點
# ════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════
#   CheckMacValue 計算
# ════════════════════════════════════════════════════════════════
def _ecpay_urlencode(s):
    """
    綠界要求的 URL encode 規則（.NET 風格）：
    - 用 quote_plus 處理（空白變 +）
    - 但保留 -_.!*() 不編碼
    - 最後轉小寫
    """
    safe_chars = "-_.!*()"
    return quote_plus(str(s), safe=safe_chars).lower()


def generate_check_mac_value(params: dict, hash_key: str, hash_iv: str) -> str:
    """
    計算綠界 CheckMacValue。

    :param params: 要送出的參數 dict（不含 CheckMacValue 本身）
    :param hash_key: 綠界提供的 HashKey
    :param hash_iv: 綠界提供的 HashIV
    :return: 大寫 SHA256 字串

    【注意】params 中若有 CheckMacValue，會先剔除再計算。
    """
    # 1. 先剔除 CheckMacValue 本身（驗證 callback 時會用到）
    filtered = {k: v for k, v in params.items() if k != "CheckMacValue"}

    # 2. 依參數名稱 A→Z 排序（不分大小寫）
    sorted_items = sorted(filtered.items(), key=lambda kv: kv[0].lower())

    # 3. 組成 key=value&key=value 字串
    body = "&".join(f"{k}={v}" for k, v in sorted_items)

    # 4. 前後加 HashKey 與 HashIV
    raw = f"HashKey={hash_key}&{body}&HashIV={hash_iv}"

    # 5. URL encode（綠界規則）→ 轉小寫
    encoded = _ecpay_urlencode(raw)

    # 6. SHA256 → 轉大寫
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest().upper()


# ════════════════════════════════════════════════════════════════
#   建立綠界結帳參數
# ════════════════════════════════════════════════════════════════
def build_checkout_params(
    *,
    merchant_id: str,
    hash_key: str,
    hash_iv: str,
    merchant_trade_no: str,
    total_amount: int,
    trade_desc: str,
    item_name: str,
    return_url: str,
    client_back_url: str,
    order_result_url: str,
) -> dict:
    """
    建立送往綠界 AIO V5 的完整參數（已含 CheckMacValue）。

    :param merchant_id:        綠界給的 MerchantID
    :param hash_key:           綠界給的 HashKey
    :param hash_iv:            綠界給的 HashIV
    :param merchant_trade_no:  你方的訂單編號（限英數，最多 20 碼）
    :param total_amount:       總金額（整數，最少 5 元）
    :param trade_desc:         交易描述（顯示用，最多 200 字）
    :param item_name:          商品名稱（多筆用 # 分隔，最多 400 字）
    :param return_url:         後端 callback 網址（Server-to-Server，POST）
    :param client_back_url:    使用者按「返回商店」會跳的網址
    :param order_result_url:   付款完成後瀏覽器跳回的網址（POST）
    :return: 含 CheckMacValue 的完整 dict，可直接放進 form 送出
    """
    params = {
        "MerchantID":        merchant_id,
        "MerchantTradeNo":   merchant_trade_no,
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType":       "aio",
        "TotalAmount":       int(total_amount),
        "TradeDesc":         trade_desc[:200],
        "ItemName":          item_name[:400],
        "ReturnURL":         return_url,
        "ChoosePayment":     "Credit",   # 只開放信用卡
        "ClientBackURL":     client_back_url,
        "OrderResultURL":    order_result_url,
        "EncryptType":       1,          # 固定填 1（SHA256）
    }

    params["CheckMacValue"] = generate_check_mac_value(params, hash_key, hash_iv)
    return params


# ════════════════════════════════════════════════════════════════
#   驗證綠界 callback 回傳的簽章
# ════════════════════════════════════════════════════════════════
def verify_callback(params: dict, hash_key: str, hash_iv: str) -> bool:
    """
    驗證綠界 callback 回傳的 CheckMacValue 是否正確。

    :param params: request.form 轉成 dict 的綠界回傳資料
    :param hash_key: 綠界 HashKey
    :param hash_iv: 綠界 HashIV
    :return: True = 簽章正確, False = 簽章不符（可能是偽造）
    """
    received_mac = params.get("CheckMacValue", "")
    if not received_mac:
        return False
    expected_mac = generate_check_mac_value(params, hash_key, hash_iv)
    return received_mac.upper() == expected_mac.upper()


# ════════════════════════════════════════════════════════════════
#   產生綠界訂單編號（MerchantTradeNo）
# ════════════════════════════════════════════════════════════════
import random
import string

def gen_merchant_trade_no(order_id: int) -> str:
    """
    產生綠界 MerchantTradeNo（限英數，最多 20 碼）。

    格式：MM + 訂單id + 時間戳後6碼 + 4碼隨機英數
    例：MM123140315X9AB
    總長度約 16~18 碼，遠低於 20 碼上限。

    【為什麼要加隨機字串】
    用公開測試金鑰 MerchantID=3002607 時，全世界開發者都在用同一個帳號測，
    訂單編號池被擠爆。純粹用「時間戳+order_id」很容易跟別人撞號，
    撞到就會出現綠界錯誤代碼 10300028「訂單編號重覆，建立失敗」。

    加 4 碼隨機英數（36^4 = 1,679,616 種組合）可大幅降低撞號機率。
    """
    ts = datetime.now().strftime("%H%M%S")  # 只用時分秒 6 碼即可
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"MM{order_id}{ts}{rand}"[:20]
