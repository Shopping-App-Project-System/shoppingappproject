 
from mcrcon import MCRcon

HOST = "localhost"
PORT = 25575
PASSWORD = "admin"

with MCRcon(HOST, PASSWORD, port=PORT) as mcr:
    result = mcr.command("/list")
    print("在線玩家：", result)
    print("RCON 連線成功！")