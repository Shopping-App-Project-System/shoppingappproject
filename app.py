from flask import Flask, render_template ,request
from db import get_db


app = Flask(__name__)

class RowObject(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"No such attribute: {name}")

@app.route("/")

#__________商品搜尋列__________
def search_categories():
    conn = get_db()

    cat_id = request.args.get('category_id', '')
    keyword = request.args.get('keyword', '')

    #分類下拉選單
    cats_result = conn.execute("SELECT pc.id ,pc.category FROM product_category pc").fetchall()
    categories = [RowObject(c) for c in cats_result]

    sql = "SELECT p.*, pc.category FROM products p JOIN product_category pc ON p.category_id = pc.id WHERE p.is_active = 1"
    params = []

    # 動態加條件
    if cat_id:
        sql += " AND p.category_id = ?"
        params.append(cat_id)
    if keyword:
        sql += " AND p.name LIKE ?"
        params.append(f"%{keyword}%")

    raw_prods = conn.execute(sql, params).fetchall()
    products = [RowObject(p) for p in raw_prods]
    
    conn.close()
    return render_template(
        "index.html", 
        products=products, 
        categories=categories)



# __________商品資訊卡__________
# 資料庫條件 -> is_active = 1 (上架)/0 (下架) 。product_quantity(庫存) > 0 

def index():

    conn = get_db()

    products = conn.execute("""

        SELECT 
            p.id,
            p.name,
            p.product_pic,
            p.original_price,
            p.sale_price,
            p.description,
            pc.category
        FROM products p

        INNER JOIN product_category pc 
            on p.category_id = pc.id
        INNER JOIN product_stock ps 
            on p.id = ps.product_id
        WHERE 
            p.is_active = 1 
            and ps.product_quantity > 0 

    """).fetchall()

    print(products)
    conn.close()

    return render_template(
        "index.html",
        products=products
    )


#__________商品詳細頁__________

@app.route("/product/<int:id>")
def product_detail(id):

    conn = get_db()

#__________查主商品__________
    product_result = conn.execute("""

        SELECT
            p.*,
            pc.category

        FROM products p

        LEFT JOIN product_category pc
        ON p.category_id = pc.id

        WHERE p.id = ?

    """, (id,)).fetchone()
    product = RowObject(product_result) if product_result else None

#__________查庫存__________
    stock_result = conn.execute("""

        SELECT *
        FROM product_stock

        WHERE product_id = ?

    """, (id,)).fetchone()
    stock = RowObject(stock_result) if stock_result else None

#__________查多圖__________
    pics_result = conn.execute("""

        SELECT product_pic
        FROM product_pics

        WHERE product_id = ?

    """, (id,)).fetchall()
    extra_pics = [RowObject(p) for p in pics_result]

    conn.close()

    # 如果沒找到商品，顯示404
    if not product:
        return "找不到該商品", 404

    return render_template(
        "product.html",
        product=product,
        stock=stock,
        extra_pics=extra_pics
    )

if __name__ == "__main__":
    app.run(debug=True)
