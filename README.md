DB record : 

branchA table columns : user_name user_mobile user_account(primary key) user_password user_email  user_address token code verify_status

branchB table columns :
    
branchC table columns :
    cart_items(id, user_account, product_id, quantity)
    orders(id, user_account, total, payment_method, delivery_method, address, note, status, created_at)
    order_items(id, order_id, product_id, quantity, price)

branchD table columns :

______________________________________________________
branchA 改善策略: 
    1.資料表無法寫入中文字
    2.token的防呆過強，已經嚴重影響使用上的體驗(只要一次重新整理頁面，驗證信就報銷了)
    3.token尚未設定過期時間
    4.驗證信發送的等待時間尚未設置
    5.防止駭客的密碼錯誤次數機制可考慮加入
    6.google authenticator totp驗證碼機制，可視情況斟酌添加
    7.輸入的資料尚未設計正則過篩機制
    8.email驗證信件內容缺乏美觀設計
    9.controler內的程式碼，可進行物件導向設計
    10.各套件需分門別類，並未後續整合後，大家的模組有地方可以歸納
    11.static/profile/temp內的資料，可設計排程或類似排成的機制去做更新，不須讓暫存區有太多太多註冊的過期資料
