DB record : 

branchA table columns : user_name user_mobile user_account(primary key) user_password user_email  user_address token code verify_status

branchB table columns :
    
branchC table columns :
    cart_items(id, user_account, product_id, quantity)
    orders(id, user_account, total, payment_method, delivery_method, address, note, status, created_at)
    order_items(id, order_id, product_id, quantity, price)

branchD table columns :
__________________________________________________________________________________________________________________________________
上傳一份資料庫可以用到的模組 : models.py
使用時機 : 所有需要下資料庫指令 對資料庫做操作時 全部都可以使用到此模組
使用方式 : 
    在與主程式同資料夾下建立一個settings.py 內部設定HOST PORT USER PASSWORD DATABASE 分別對應到自己使用的資料庫資訊
    將models.py放在與主程式同資料夾中
    1. from models import Models # 從模組中引入Models類別
    2. model = Models() # 對類別初始化
    3. 在類別內部創建類別方法 並使用@start裝飾器 即可順利完成
       example :
           @start
           def test(self,cursor):
               sursor.execute(""" instructions """)
               .
               .
               .
               return 
    4. 如果要傳入參數 用法如下
       example :
           model.test("account","password")
    5. 而方法宣告上 第一個參數一定要是cursor 後面即對應到傳入的參數
參考 :
    token = model.getVerifyToken(user_account)
    ==================================================
    @start
    def getVerifyToken(self,cursor,account): # 因指令中需要用到account 因此傳遞參數user_account 並用引數account承接
        cursor.execute("""
                                SELECT `verify_token`
                                FROM register_table
                                WHERE `account` = ?
                            """,(account,)) # 資料庫的操作
        token = cursor.fetchone() # 取得資料
        if token is None:
            return token
        return token[0] # 回傳結果
