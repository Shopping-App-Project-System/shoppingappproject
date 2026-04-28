# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 07:36:28 2026

@author: eric2
"""

#HTML
#會員資料
<form action="/member/profile" method="POST">
    <div class="field">
        <label>姓名</label>
        <input type="text" name="name" value="{{ member.name }}">
    </div>
    <div class="field">
        <label>電話</label>
        <input type="text" name="phone" value="{{ member.phone }}">
    </div>
    <button type="submit">儲存變更</button>
</form>
#歷史購物紀錄
<table>
    <thead>
        <tr><th>訂單日期</th><th>總金額</th><th>狀態</th></tr>
    </thead>
    <tbody>
        {% for order in orders %}
        <tr>
            <td>{{ order.date }}</td>
            <td>${{ order.total }}</td>
            <td>{{ order.status }}</td>
        </tr>
        {% else %}
        <tr>
            <td colspan="3">目前尚無購物紀錄</td>
        </tr>
        {% endfor %}
    </tbody>
</table>