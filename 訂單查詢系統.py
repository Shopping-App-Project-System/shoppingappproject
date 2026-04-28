# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 06:03:53 2026

@author: eric2
"""

#訂單查詢系統
from datetime import datetime

class Order:
    def __init__(self, order_id, items, summary, status="處理中"):
        self.order_id = order_id
        self.items = items  # 購買時的商品快照 (List of dicts)
        self.summary = summary # 購買時的金額快照
        self.status = status
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_view_dict(self):
        """專門為 order_lookup.html 準備的資料"""
        return {
            "id": self.order_id,
            "date": self.created_at,
            "items_count": len(self.items),
            "total": self.summary['total'],
            "status": self.status
        }