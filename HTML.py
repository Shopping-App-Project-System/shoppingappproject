# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 06:11:50 2026

@author: eric2
"""

#HTML
#圖片上傳表單 (後端管理介面)
<form action="/admin/product/add" method="POST" enctype="multipart/form-data">
    <input type="text" name="name" placeholder="商品名稱" required>
    <input type="number" name="price" placeholder="價格" required>
    <input type="file" name="image"> <button type="submit">上架商品</button>
</form>
#訂單查詢頁面
<div class="search-box">
    <h2>查詢您的訂單</h2>
    <form action="/order/search" method="GET">
        <input type="text" name="id" placeholder="請輸入訂單編號 (例如: #1001)">
        <button type="submit">立即查詢</button>
    </form>
    
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
</div>