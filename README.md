DB record : 

branchA table columns : name mobile account(primary key) password email  address token code verify_status

branchB table columns :
    
branchC table columns :
    cart_items(id, user_account, product_id, quantity)
    orders(id, user_account, total, payment_method, delivery_method, address, note, status, created_at)
    order_items(id, order_id, product_id, quantity, price)

branchD table columns :
