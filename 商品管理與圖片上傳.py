# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#商品管理與圖片上傳
import os
from werkzeug.utils import secure_filename

class Product:
    def __init__(self, p_id, name, price, img_filename=None):
        self.p_id = p_id
        self.name = name
        self.price = price
        # 存儲於資料庫的通常只是檔名
        self.img_path = f"/static/uploads/{img_filename}" if img_filename else "/static/default.png"

class ProductManager:
    UPLOAD_FOLDER = 'static/uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self):
        self.products = [] # 實際開發時應串接資料庫

    def save_image(self, file):
        """處理圖片上傳並回傳檔名"""
        if file and self._allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 確保資料夾存在
            os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(self.UPLOAD_FOLDER, filename))
            return filename
        return None

    def _allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    