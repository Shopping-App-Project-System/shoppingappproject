"""使用者帳號與登入狀態。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import BRANCH_A_TABLE


@db_transaction
def createUser(cursor, user_account, user_password, user_email):
    # 新增會員帳號
    cursor.execute(f"""
        INSERT INTO {BRANCH_A_TABLE}
        (`user_account`,`user_password`,`user_email`)
        VALUES (%s,%s,%s)
    """, (user_account, user_password, user_email))


@db_transaction
def updateUser(cursor, set_: dict, where: dict):
    # 更新會員資料，set_ 為要更新的欄位，where 為篩選條件
    set_key, set_value = tuple(set_.keys()), tuple(set_.values())
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    set_sql = ", ".join(f"`{key}` = %s" for key in set_key)
    where_sql = " AND ".join(f"`{key}` = %s" for key in where_key)

    cursor.execute(f"""
        UPDATE {BRANCH_A_TABLE}
        SET {set_sql}
        WHERE {where_sql}
    """, set_value + where_value)


@db_transaction
def getUser(cursor, where: dict, *selections):
    # 依條件查詢會員資料，selections 為要取得的欄位，不傳則取全部
    # 只有一個欄位時直接回傳值，多個欄位回傳 dict，找不到回傳 None
    where_key, where_value = tuple(where.keys()), tuple(where.values())

    if selections == ():
        selections = "*"
    else:
        selections = ",".join(f"`{selection}`" for selection in selections)

    where_sql = " AND ".join(f"`{key}` = %s" for key in where_key)

    cursor.execute(f"""
        SELECT {selections}
        FROM {BRANCH_A_TABLE}
        WHERE {where_sql}
    """, where_value)

    users = cursor.fetchall()
    if users:
        users = users[0]
        if len(users) == 1:
            return list(users.values())[0]
        return users
    return None


@db_transaction
def getUserList(cursor, *selections):
    """
    取得所有會員清單。

    :param selections: 可變數欄位名（類似 getUser），不傳則取全部欄位。
                       例：getUserList("user_account", "user_email")
                       將回傳 [{"user_account": ..., "user_email": ...}, ...]

    :return: 一律回傳 list of dict；若資料表沒有會員，回傳空 list []。
             即使只指定一個欄位，也維持 list of dict 結構，
             方便上層用 `any(u[field] == value for u in users)` 比對。

    使用情境：
        register_service 在註冊時要檢查「帳號 / 信箱是否已被使用」，
        會抓出所有會員的帳號與信箱清單做比對。

    【效能小提醒】
    會員一多時，逐筆查詢 (getUser) 會比抓整張表來得有效率。
    若 user_account / user_email 在資料庫已加 UNIQUE 索引，
    更建議直接用 getUser 二次查詢來判斷重複。
    """
    if selections == ():
        selections = "*"
    else:
        selections = ",".join(f"`{selection}`" for selection in selections)

    cursor.execute(f"""
        SELECT {selections}
        FROM {BRANCH_A_TABLE}
    """)
    return cursor.fetchall()


@db_transaction
def updateSessionToken(cursor, session_token, session_expires_at, account):
    cursor.execute(f"""
        UPDATE {BRANCH_A_TABLE}
        SET session_token = %s, session_expires_at = %s
        WHERE user_account = %s
    """, (session_token, session_expires_at, account))


@db_transaction
def clearSessionToken(cursor, account):
    cursor.execute(f"""
        UPDATE {BRANCH_A_TABLE}
        SET session_token = NULL, session_expires_at = NULL
        WHERE user_account = %s
    """, (account,))


@db_transaction
def get_user_minecraft_name(cursor, user_account):
    # 取得會員綁定的 Minecraft 角色名
    cursor.execute(
        f"SELECT minecraft_name FROM `{BRANCH_A_TABLE}` WHERE user_account = %s",
        (user_account,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row['minecraft_name'] if isinstance(row, dict) else row[0]
