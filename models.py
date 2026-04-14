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
        except:
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
    
    def _init_db(self):
        conn = mariadb.connect(host=self.HOST, port=self.PORT,
                               user=self.USER, password=self.PASSWORD,
                               database=self.DATABASE)
        cursor = conn.cursor()
        # 商品表（由其他 Branch 負責寫入，Branch C 只做 JOIN 讀取）
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS products (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                name       VARCHAR(255) NOT NULL,
                price      DECIMAL(10,2) NOT NULL,
                image_path VARCHAR(255)
            )'''
        )
        # 購物車表
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS cart_items (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                user_account VARCHAR(255) NOT NULL,
                product_id   INT NOT NULL,
                quantity     INT NOT NULL DEFAULT 1
            )'''
        )
        # 訂單主檔
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS orders (
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
            '''CREATE TABLE IF NOT EXISTS order_items (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                order_id   INT NOT NULL,
                product_id INT NOT NULL,
                quantity   INT NOT NULL,
                price      DECIMAL(10,2) NOT NULL
            )'''
        )
        # 若 products 是空的，插入測試商品（測試用，整合後由其他 Branch 管理）
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO products (name, price, image_path) VALUES (?, ?, NULL)",
                [("測試商品A", 100), ("測試商品B", 250), ("測試商品C", 500)]
            )
        conn.commit()
        cursor.close()
        conn.close()

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


    # ── 購物車 (Branch C) ────────────────────────────────────────────────────────

    @start
    def get_cart_items(self, cursor, user_account):
        # 查詢使用者購物車，JOIN products 取得商品名稱、價格、圖片路徑
        # 回傳：list of dict，每筆含 id, product_id, quantity, name, price, image_path
        cursor.execute(
            '''SELECT c.id, c.user_account, c.product_id, c.quantity,
                      p.name, p.price, p.image_path
               FROM cart_items c
               JOIN products p ON c.product_id = p.id
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
        # 新增商品到購物車
        # 若該使用者購物車已有此商品，則數量 +1；否則新增數量為 1 的記錄
        cursor.execute(
            'SELECT id, quantity FROM cart_items WHERE user_account=? AND product_id=?',
            (user_account, product_id)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                'UPDATE cart_items SET quantity=? WHERE id=?',
                (existing[1] + 1, existing[0])
            )
        else:
            cursor.execute(
                'INSERT INTO cart_items (user_account, product_id, quantity) VALUES (?,?,1)',
                (user_account, product_id)
            )

    @start
    def remove_cart_item(self, cursor, item_id, user_account):
        # 刪除購物車中指定項目，同時比對 user_account 確保只能刪除自己的項目
        cursor.execute(
            'DELETE FROM cart_items WHERE id=? AND user_account=?',
            (item_id, user_account)
        )

    @start
    def clear_cart(self, cursor, user_account):
        # 清空指定使用者的整個購物車，通常在訂單建立成功後呼叫
        cursor.execute(
            'DELETE FROM cart_items WHERE user_account=?',
            (user_account,)
        )


    # ── 訂單 (Branch C) ──────────────────────────────────────────────────────────

    @start
    def create_order(self, cursor, user_account, total, payment_method,
                     delivery_method, address, note, items):
        # 建立訂單主檔（status 預設「處理中」），再逐一寫入每筆訂單明細
        # 回傳：新訂單的 id（整數）
        cursor.execute(
            '''INSERT INTO orders
               (user_account, total, payment_method, delivery_method, address, note, status)
               VALUES (?,?,?,?,?,?,'處理中')''',
            (user_account, total, payment_method, delivery_method, address, note)
        )
        order_id = cursor.lastrowid
        for item in items:
            cursor.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)',
                (order_id, item['product_id'], item['quantity'], item['price'])
            )
        return order_id

    @start
    def get_orders(self, cursor, user_account):
        # 查詢指定使用者的所有歷史訂單，依建立時間由新到舊排列
        # 回傳：list of dict
        cursor.execute(
            '''SELECT id, total, payment_method, delivery_method,
                      address, note, status, created_at
               FROM orders
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
            '''SELECT id, total, payment_method, delivery_method,
                      address, note, status, created_at
               FROM orders
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


"""
於此做測試程式碼
外部匯入此模組時
只有模組內操作時才會被執行
外部不會執行到
"""
if __name__ == "__main__":
    ...
