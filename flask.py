# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 07:27:51 2026

@author: eric2
"""

#flask
@app.route("/member/profile", methods=["GET", "POST"])
def edit_profile():
    # 假設從 session 獲取當前登入者
    user_id = session.get("user_id")
    member = current_user_db.get(user_id) 

    if request.method == "POST":
        # 處理修改資料
        member_service.update_profile(member, request.form)
        return redirect("/member/profile") # 修改後導回，防止重複提交

    return render_template("member_profile.html", member=member.to_dict())

@app.route("/member/orders")
def view_history():
    user_id = session.get("user_id")
    orders = member_service.get_order_history(user_id)
    
    return render_template("member_orders.html", orders=[o.to_view_dict() for o in orders])