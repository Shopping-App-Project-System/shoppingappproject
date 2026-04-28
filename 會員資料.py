# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 07:23:25 2026

@author: eric2
"""

#會員資料
class Member:
    def __init__(self, user_id, name, email, phone=""):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone

    def update_info(self, name, phone):
        """會員修改資料的邏輯"""
        self.name = name
        self.phone = phone

    def to_dict(self):
        return {
            "id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone
        }
#歷史購物資料
class MemberService:
    def __init__(self, all_orders):
        self.all_orders = all_orders  # 模擬全域訂單庫

    def get_order_history(self, user_id):
        """根據會員 ID 過濾出該會員的所有訂單"""
        user_orders = [o for o in self.all_orders.values() if o.user_id == user_id]
        return user_orders

    def update_profile(self, member_obj, new_data):
        """執行修改並寫入資料庫(模擬)"""
        member_obj.update_info(new_data.get('name'), new_data.get('phone'))
        # 這裡未來應串接 DB commit