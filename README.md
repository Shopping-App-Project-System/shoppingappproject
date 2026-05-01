Note:

1. 整合各分支內容
2. 程式碼改寫（由於改動很多，後續會做指南讓大家看）
3. 取消 model 類別，全部改為一般 function
4. 拆分資料庫方法（資料庫內一個指令 for 一個 function，"只有取值功能"，其他邏輯全部給 controller 操作）
5. 資料庫 cursor 加入 `dictionary=True` 設定，回傳值變成 dict 資料型態（對應修改已完成）
6. 帶入模組化設計（使用 flask 提供的 Blueprint 模組）
7. 路由的功能會拉出來
8. 取值方式會包裝成裝飾器，裝飾路由的功能 function
   - 其功能：取出來的值會放在 function 的小括號內
   - 並且加入例外處理 → 不可能完成後使用者用一下就 break :D
9. 會另外做一個頁面，承接錯誤訊息（類似於：您好，系統繁忙中，請稍後再試 → 3 秒後自動跳轉首頁）
10. 目前增加了：
    - 會員資料可修改
    - 取消會員中心的收件者資訊 → 原因是這個資訊並不固定，都是購買當下指定，預設是註冊資料
    - 增加 log 資料表 → 後台可管理訂單資料狀態，且這部分跟前台分離不相干

---

## DB record

### branchA table columns
| 欄位 |
|------|
| user_name |
| user_mobile |
| user_account (primary key) |
| user_password |
| user_email |
| user_address |
| token |
| code |
| verify_status |

### branchB table columns

**商品資訊**（id、產品名稱、商品圖、定價、活動價、商品描述、商品分類、上架狀態（預設 0 下架／1 上架）、活動標籤、條碼）
```sql
products(id, product_id, product_pic, original_price, sale_price, description, category, is_active, tag, barcode)
```

**商品多圖展示**（id、產品名稱、商品圖）→ 如果有要做多圖展示可以用
```sql
product_pics(id, product_id, product_pic)
```

**商品分類**（id、商品分類）
```sql
product_category(id, product_id, category)
```

**活動標籤**（id、產品名稱、標籤）→ ex. 新品、熱銷、特賣
```sql
active_tag(id, product_id, tag)
```

**庫存清單**（id、產品名稱、庫存量、入庫量、出庫量）
```sql
product_stock(id, product_id, product_quantity, inbound, outbound)
```

### branchC table columns

```sql
cart_items(id, user_account, product_id, quantity)
orders(id, user_account, total, payment_method, delivery_method, address, note, status, created_at)
order_items(id, order_id, product_id, quantity, price)
```

### branchD table columns