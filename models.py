import mariadb
from functools import wraps
import settings

"""
此為裝飾器 在撰寫程式碼中 可以不必理會
功能 :
    在類別方法中 使用此裝飾器 即可取得 -
        '自動建立consor 、 自動關閉 、 錯誤時自動回朔以避免資料毀損' 之效用
"""
def start(fun):
    @wraps(fun)
    def wrap(self,*args,**kwargs):
        conn = mariadb.connect(host=self.HOST, port=self.PORT,
                user=self.USER, password=self.PASSWORD,
                database=self.DATABASE)
        cursor = conn.cursor()
        try:
            result = fun(self,cursor,*args,**kwargs)
            conn.commit()
            return result
        except Exception as e:
            raise e
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    return wrap

"""
建立方式 : 先在settings.py中的DATABASE變數中 設定你的資料庫連線資訊
           在controler.py中 使用以下程式碼用於匯入模組
               from models import Models
           然後在初始化的區塊中 寫入以下程式碼
               model = Models()
"""
class Models:
    def __init__(self):
        self.HOST = settings.HOST
        self.PORT = settings.PORT
        self.USER = settings.USER
        self.PASSWORD = settings.PASSWORD
        self.DATABASE = settings.DATABASE
        self._init_db()

    @start
    def _init_db(self, cursor):
        # 測試用 使用者表
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS `{settings.BRANCH_A_TABLE}` (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                user_name      VARCHAR(255) NOT NULL,
                user_account   VARCHAR(255) NOT NULL UNIQUE,
                user_password  VARCHAR(255) NOT NULL,
                user_mobile    VARCHAR(50),
                user_email     VARCHAR(255),
                user_address   VARCHAR(255),
                pic_path       VARCHAR(255),
                token          VARCHAR(255),
                code           VARCHAR(20),
                verify_status  BOOLEAN DEFAULT FALSE
            )'''
        )
        # 測試用 商品表
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS `{settings.BRANCH_B_TABLE}` (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                name       VARCHAR(255) NOT NULL,
                price      DECIMAL(10,2) NOT NULL,
                image_path VARCHAR(255)
            )'''
        )
        # 購物車表
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS `{settings.BRANCH_C_CART_TABLE}` (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                user_account VARCHAR(255) NOT NULL,
                product_id   INT NOT NULL,
                quantity     INT NOT NULL DEFAULT 1
            )'''
        )
        # 訂單主檔
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS `{settings.BRANCH_C_ORDER_TABLE}` (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                user_account    VARCHAR(255) NOT NULL,
                total           DECIMAL(10,2) NOT NULL,
                payment_method  VARCHAR(50),
                delivery_method VARCHAR(50),
                address         VARCHAR(255),
                note            TEXT,
                status          VARCHAR(50) DEFAULT '處理中',
                created_at      DATETIME DEFAULT NOW()
            )'''
        )
        # 訂單明細表
        cursor.execute(
            f'''CREATE TABLE IF NOT EXISTS `{settings.BRANCH_C_ORDER_ITEMS_TABLE}` (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                order_id   INT NOT NULL,
                product_id INT NOT NULL,
                quantity   INT NOT NULL,
                price      DECIMAL(10,2) NOT NULL
            )'''
        )

    """
    範例:
        函式名稱 : 取決於你想做的功能 依照功能或回傳的東西做命名 以便於解讀為主
        使用方式 : 第一個參數固定為'self' 第二個參數固定為'consor' 後面的參數為'你想在這個資料庫操作中用那些外來的值'
                --- 例如 ---
                    若需要用account來找相對應的資料
                    model = models.Models()
                    datas = model.test(account)
                    ___________________________________
                    則建立時 則撰寫:
                        @start # 此為使用上方裝飾器的方法 可以當作固定的標配(只要撰寫類別方法 就直接使用)
                        def test(self,consor,account_example):
                            ...
                            ...
                            寫入你需要操作的程式碼
                            ...
                            ...
                            return ...

    """
    # _____________________________write into your code_____________________________________

    # ── Branch A：使用者帳號相關方法 ────────────────────────────────────────────────────

    # 新增使用者（不含 pic_path、token、code，待後續 updateUser 補上）
    @start
    def createUser(self,cursor,user_name,user_account,user_password,user_mobile,user_email,user_address):
        cursor.execute(f"""
                                INSERT INTO `{settings.BRANCH_A_TABLE}`
                                (`user_name`,`user_account`,`user_password`,`user_mobile`,`user_email`,`user_address`)
                                VALUES (?,?,?,?,?,?)
                            """,(user_name,user_account,user_password,user_mobile,user_email,user_address))
    

    # 動態更新使用者欄位：set_ 為要更新的欄位 dict，where 為條件 dict，自動組成 UPDATE SQL
    @start
    def updateUser(self, cursor, set_: dict, where: dict):
        set_key, set_value = tuple(set_.keys()), tuple(set_.values())
        where_key, where_value = tuple(where.keys()), tuple(where.values())
    
        set_sql = ", ".join(f"`{key}` = ?" for key in set_key)
        where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)
    
        cursor.execute(f"""
                            UPDATE `{settings.BRANCH_A_TABLE}`
                            SET {set_sql}
                            WHERE {where_sql}
                        """, set_value + where_value)
    

    # 查詢使用者：where 為條件 dict，selections 為欲取得的欄位（不傳則 SELECT *）
    # 回傳單筆，單欄位直接回傳值，多欄位回傳 tuple，查無資料回傳 None
    @start
    def getUser(self, cursor, where: dict, *selections):
        where_key, where_value = tuple(where.keys()), tuple(where.values())
    
        if selections == ():
            selections = "*"
        else:
            selections = ",".join(f"`{selection}`" for selection in selections)
    
        where_sql = " AND ".join(f"`{key}` = ?" for key in where_key)
    
        cursor.execute(f"""
                            SELECT {selections}
                            FROM `{settings.BRANCH_A_TABLE}`
                            WHERE {where_sql}
                        """, where_value)
    
        users = cursor.fetchall()
        if users != []:
            users = users[0]
            if len(users) == 1:
                return users[0]
            return users
        return None
    
    # ── Branch B：商品相關方法 ────────────────────────────────────────────────────────

    # 取得所有商品清單，每筆包含 id、名稱、價格、圖片路徑，以及加入購物車的 URL
    @start
    def get_products(self, cursor):
        cursor.execute(f'SELECT id, name, price, image_path FROM `{settings.BRANCH_B_TABLE}`')
        rows = cursor.fetchall()
        return [
            {
                'id'      : r[0],
                'name'    : r[1],
                'price'   : r[2],
                'image_url': r[3],
                'cart_url': f"/cart/add?product_id={r[0]}"
            }
            for r in rows
        ]

    # ── Branch C：購物車 ──────────────────────────────────────────────────────────

    @start
    def get_cart_items(self, cursor, user_account):
        # 查詢使用者購物車，JOIN products 取得商品名稱、價格、圖片路徑
        # 回傳：list of dict，每筆含 id, product_id, quantity, name, price, image_path
        cursor.execute(
            f'''SELECT c.id, c.user_account, c.product_id, c.quantity,
                       p.name, p.price, p.image_path
                FROM `{settings.BRANCH_C_CART_TABLE}` c
                JOIN `{settings.BRANCH_B_TABLE}` p ON c.product_id = p.id
                WHERE c.user_account = ?''',
            (user_account,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id'          : row[0],
                'user_account': row[1],
                'product_id'  : row[2],
                'quantity'    : row[3],
                'name'        : row[4],
                'price'       : row[5],
                'image_path'  : row[6],
            })
        return result

    @start
    def add_cart_item(self, cursor, user_account, product_id):
        # 先確認商品存在，防止寫入孤立資料；不存在回傳 False
        # 已有此商品則數量 +1，否則新增數量為 1 的記錄，回傳商品名稱
        cursor.execute(
            f'SELECT id, name FROM `{settings.BRANCH_B_TABLE}` WHERE id=?',
            (product_id,)
        )
        product = cursor.fetchone()
        if product is None:
            return False
        product_name = product[1]

        cursor.execute(
            f'SELECT id, quantity FROM `{settings.BRANCH_C_CART_TABLE}` WHERE user_account=? AND product_id=?',
            (user_account, product_id)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                f'UPDATE `{settings.BRANCH_C_CART_TABLE}` SET quantity=? WHERE id=?',
                (existing[1] + 1, existing[0])
            )
        else:
            cursor.execute(
                f'INSERT INTO `{settings.BRANCH_C_CART_TABLE}` (user_account, product_id, quantity) VALUES (?,?,1)',
                (user_account, product_id)
            )
        return product_name

    @start
    def remove_cart_item(self, cursor, item_id, user_account):
        # 刪除購物車中指定項目，同時比對 user_account 確保只能刪除自己的項目
        cursor.execute(
            f'DELETE FROM `{settings.BRANCH_C_CART_TABLE}` WHERE id=? AND user_account=?',
            (item_id, user_account)
        )

    @start
    def clear_cart(self, cursor, user_account):
        # 清空指定使用者的整個購物車，通常在訂單建立成功後呼叫
        cursor.execute(
            f'DELETE FROM `{settings.BRANCH_C_CART_TABLE}` WHERE user_account=?',
            (user_account,)
        )

    # ── Branch C：訂單 ────────────────────────────────────────────────────────────

    @start
    def create_order(self, cursor, user_account, total, payment_method,
                     delivery_method, address, note, items):
        # 建立訂單主檔（status 預設「處理中」），再逐一寫入每筆訂單明細
        # 回傳：新訂單的 id（整數）
        cursor.execute(
            f'''INSERT INTO `{settings.BRANCH_C_ORDER_TABLE}`
                (user_account, total, payment_method, delivery_method, address, note, status)
                VALUES (?,?,?,?,?,?,'處理中')''',
            (user_account, total, payment_method, delivery_method, address, note)
        )
        order_id = cursor.lastrowid
        for item in items:
            cursor.execute(
                f'INSERT INTO `{settings.BRANCH_C_ORDER_ITEMS_TABLE}` (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
                (order_id, item['product_id'], item['quantity'], item['price'])
            )
        return order_id

    @start
    def get_orders(self, cursor, user_account):
        # 查詢指定使用者的所有歷史訂單，依建立時間由新到舊排列
        # 回傳：list of dict
        cursor.execute(
            f'''SELECT id, total, payment_method, delivery_method,
                       address, note, status, created_at
                FROM `{settings.BRANCH_C_ORDER_TABLE}`
                WHERE user_account=?
                ORDER BY created_at DESC''',
            (user_account,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id'             : row[0],
                'total'          : row[1],
                'payment_method' : row[2],
                'delivery_method': row[3],
                'address'        : row[4],
                'note'           : row[5],
                'status'         : row[6],
                'created_at'     : row[7],
            })
        return result

    @start
    def search_orders(self, cursor, user_account, keyword):
        # 以關鍵字搜尋指定使用者的訂單
        # 使用 LIKE 搭配 % 萬用字元，比對收件地址或訂單狀態是否包含關鍵字
        like_keyword = "%" + keyword + "%"
        cursor.execute(
            f'''SELECT id, total, payment_method, delivery_method,
                       address, note, status, created_at
                FROM `{settings.BRANCH_C_ORDER_TABLE}`
                WHERE user_account = ?
                  AND (address LIKE ? OR status LIKE ?)
                ORDER BY created_at DESC''',
            (user_account, like_keyword, like_keyword)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id'             : row[0],
                'total'          : row[1],
                'payment_method' : row[2],
                'delivery_method': row[3],
                'address'        : row[4],
                'note'           : row[5],
                'status'         : row[6],
                'created_at'     : row[7],
            })
        return result


    @start
    def cancel_order(self, cursor, order_id, user_account):
        # 取消訂單：僅允許取消屬於該使用者且狀態為「處理中」的訂單
        # 回傳 True 表示成功，False 表示訂單不存在或無權限或已非處理中
        cursor.execute(
            f'''SELECT id FROM `{settings.BRANCH_C_ORDER_TABLE}`
                WHERE id=? AND user_account=? AND status='處理中' ''',
            (order_id, user_account)
        )
        if cursor.fetchone() is None:
            return False
        cursor.execute(
            f"UPDATE `{settings.BRANCH_C_ORDER_TABLE}` SET status='已取消' WHERE id=?",
            (order_id,)
        )
        return True

"""
於此做測試程式碼
外部匯入此模組時
只有模組內操作時才會被執行
外部不會執行到
"""
if __name__ == "__main__":
    ...