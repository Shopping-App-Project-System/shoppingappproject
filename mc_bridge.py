# mc_bridge.py
# =========================================================
# 【說明】
#   此檔案負責所有與 Minecraft RCON 的通訊。
#   give_item / notify_player 由 Shopping_services 直接呼叫。
#
# 【設計決策】
#   user_account 本身就是 Minecraft ID（註冊時強制符合格式），
#   所以不需要另外查資料庫，直接當玩家名稱使用。
#
# 【備用設計（已在 models.py 中註解保留）】
#   若未來要改成「user_account 與 Minecraft ID 分離」的設計，
#   可以參考 models.py 裡被註解的區塊：
#     - get_user_minecraft_name：查資料庫 minecraft_name 欄位
#     - give_item（舊版）：查名稱 + 驗證在線 + 發道具
#     - notify_player（舊版）：查名稱 + 發訊息
#     - deliver_cart_to_player：整批發貨
#   那個版本需要在 user 資料表加回 minecraft_name 欄位。
# =========================================================

from mcrcon import MCRcon
from settings import MC_RCON_HOST, MC_RCON_PORT, MC_RCON_PASSWORD

HOST     = MC_RCON_HOST
PORT     = MC_RCON_PORT
PASSWORD = MC_RCON_PASSWORD


def send_mc_command(command: str):
    """送出一個 RCON 指令"""
    try:
        with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
            response = mcr.command(command)
            print(f"[MC] ✓ {command!r} → {response!r}")
            return True
    except Exception as e:
        print(f"[MC] ✗ 指令失敗: {e}")
        return False


def notify_player(mc_username: str, message: str):
    """
    私訊玩家。
    mc_username 直接傳 user_account，
    因為註冊時強制使用 Minecraft ID 格式，兩者相同。
    """
    send_mc_command(f'tellraw {mc_username} {{"text":"{message}","color":"green"}}')


def give_item(user_account: str, mc_item_id: str, quantity: int = 1, nbt=None):
    """
    給予道具。
    user_account 直接當 Minecraft 玩家名稱，不需要查資料庫。
    （因為註冊時 user_account 強制符合 Minecraft ID 格式）

    若未來改成雙帳號設計（網站帳號 ≠ MC 名稱），
    請改回 models.py 裡被註解的舊版 give_item，
    並在 user 資料表加回 minecraft_name 欄位。
    """
    if nbt:
        cmd = f"give {user_account} {mc_item_id}{nbt} {quantity}"
    else:
        cmd = f"give {user_account} {mc_item_id} {quantity}"
    send_mc_command(cmd)
