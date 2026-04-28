# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 06:08:26 2026

@author: eric2
"""

#Flask 路由整合實作
from flask import Flask, render_template, request, redirect

app = Flask(__name__)
pm = ProductManager()
orders_db = {} # 模擬訂單資料庫 {order_id: Order物件}

# --- 商品管理：新增商品 (含圖片上傳) ---
@app.route("/admin/product/add", methods=["POST"])
def add_product():
    name = request.form.get("name")
    price = request.form.get("price")
    file = request.files.get("image")
    
    # 處理圖片並取得路徑
    img_filename = pm.save_image(file)
    
    # 建立商品並存入「資料庫」
    new_p = Product(len(pm.products)+1, name, price, img_filename)
    pm.products.append(new_p)
    
    return redirect("/cart")

# --- 訂單查詢：查看特定訂單 ---
@app.route("/order/search")
def order_search():
    order_id = request.args.get("id")
    order = orders_db.get(order_id)
    
    if not order:
        return render_template("order_query.html", error="找不到該訂單編號")
        
    return render_template("order_detail.html", order=order.to_view_dict())