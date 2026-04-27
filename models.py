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
    # _____________________________商品搜尋列_____________________________________
    
    @start
    def search_categories(self, consor, cat_id, keyword):
        sql = """
            SELECT p.*,pc.category
            FROM products p
            JOIN product_category pc 
            ON p.category_id = pc.id
            WHERE p.is_active = 1
        """
        params = []

        if cat_id:
            sql += " AND p.category_id = %s"
            params.append(cat_id)
        if keyword:
            sql += " AND p.name LIKE %s"
            params.append(f"%{keyword}%")        
        
        consor.execute(sql,params)
        results = consor.fetchall()
        return [RowObject(r) for r in results]
    
    @start
    def get_all_categories(self, consor):
        consor.execute("SELECT id, category FROM product_category")
        results = consor.fetchall()
        return [RowObject(r) for r in results]


    # _____________________________商品資訊卡_____________________________________
    # 資料庫條件 -> is_active = 1 (上架)/0 (下架) 。product_quantity(庫存) > 0 

    @start
    def index(self, consor):
        sql_query = """
            SELECT 
                p.id,
                p.name,
                p.product_pic,
                p.original_price,
                p.sale_price,
                p.description,
                pc.category
            FROM products p
            INNER JOIN product_category pc
                on p.category_id = pc.id
            INNER JOIN product_stock ps 
                on p.id = ps.product_id
            WHERE 
                p.is_active = 1 
                and ps.product_quantity > 0 
        """

        consor.execute(sql_query)
        results = consor.fetchall()
        return [RowObject(r) for r in results]
    
    # _____________________________商品詳細頁_____________________________________
  
    @start
    def product_detail(self, consor, product_id):
        #__________查主商品__________
        sql_product = """
            SELECT
                p.*,
                pc.category
            FROM products p
            LEFT JOIN product_category pc
            ON p.category_id = pc.id
            WHERE p.id = %s
        """
    
        consor.execute(sql_product, (product_id,))
        results_product = consor.fetchall()
        product = RowObject(results_product) if results_product else None

        if not product:
            return None, None, []
        
        #__________查庫存__________
        sql_stock = "SELECT * FROM product_stock WHERE product_id = %s"
        consor.execute(sql_stock, (product_id,))
        res_s = consor.fetchone()
        stock = RowObject(res_s) if res_s else None     

        #__________查多圖__________
        sql_pics = "SELECT product_pic FROM product_pics WHERE product_id = %s"
        consor.execute(sql_pics, (product_id,))
        res_pics = consor.fetchall()
        extra_pics = [RowObject(p) for p in res_pics]

        return product, stock, extra_pics
    
"""
於此做測試程式碼
外部匯入此模組時
只有模組內操作時才會被執行
外部不會執行到
"""
if __name__ == "__main__":
    ...