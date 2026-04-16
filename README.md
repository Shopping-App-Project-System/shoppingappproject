DB record : 

branchA table columns : user_name user_mobile user_account(primary key) user_password user_email  user_address pic_path token code verify_status

branchB table columns :

    商品資訊 ( id 、產品名稱、商品圖、定價、活動價、商品描述、商品分類、上架狀態(預設0下架/1為上架)、活動標籤、條碼)
    products(id, product_id, product_pic, original_price, sale_price, description, category,is_active, tag, barcode)
    
    商品多圖展示(id 、產品名稱、商品圖) ->如果有要做多圖的展示可以用
    product_pics (id, product_id, product_pic)
    
    商品分類 (id、商品分類)
    product_category(id, product_id,category )
    
    活動標籤 (id、產品名稱、標籤)->(ex. 新品、熱銷、特賣)
    active_tag(id, product_id,tag )
    
    庫存清單(id、產品名稱、庫存量、入庫量、出庫量)
    product_stock(id, product_id, product_quantity, inbound, outbound )
    
branchC table columns :
    cart_items(id, user_account, product_id, quantity)
    orders(id, user_account, total, payment_method, delivery_method, address, note, status, created_at)
    order_items(id, order_id, product_id, quantity, price)

branchD table columns :
