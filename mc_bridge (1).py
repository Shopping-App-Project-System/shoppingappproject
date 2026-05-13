# mc_bridge.py
from mcrcon import MCRcon
from settings import MC_RCON_HOST,MC_RCON_PORT,MC_RCON_PASSWORD
HOST     = MC_RCON_HOST
PORT     = MC_RCON_PORT
PASSWORD = MC_RCON_PASSWORD

def send_mc_command(command: str):
    """送出一個 RCON 指令，回傳伺服器回應"""
    try:
        with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
            response = mcr.command(command)
            print(f"[MC] ✓ {command!r} → {response!r}")
            return True
    except Exception as e:
        print(f"[MC] ✗ 指令失敗: {e}")
        return False

def notify_player(mc_username: str, message: str):
    """私訊玩家"""
    send_mc_command(f'tellraw {mc_username} {{"text":"{message}","color":"green"}}')

def give_item(mc_username: str, item_id: str, amount: int = 1):
    """給予道具"""
    send_mc_command(f"give {mc_username} {item_id} {amount}")