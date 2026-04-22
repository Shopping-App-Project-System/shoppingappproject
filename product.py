from flask import Flask, render_template, redirect, url_for, session
from database.fake_data import products

app = Flask(__name__)
app.secret_key = "your_secret_key"


#______________首頁______________
@app.route("/")
def index():

    for product in products:
        product["detail_url"] = url_for("product_detail", product_id=product["id"])
        product["cart_url"] = url_for("add_to_cart", product_id=product["id"])

    return render_template(
        "index.html",
        products=products,
        store_name="My Store"
    )


#______________商品詳細頁______________
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if not product:
        return "商品不存在"

    return render_template(
        "product.html",
        product=product,
        store_name="My Store"
    )


#______________加入購物車______________
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append(product_id)

    session.modified = True

    return redirect(url_for("cart"))


#______________購物車頁______________
@app.route("/cart")
def cart():

    cart_ids = session.get("cart", [])

    cart_products = [
        p for p in products if p["id"] in cart_ids
    ]

    return render_template(
        "cart.html",
        cart_products=cart_products
    )


if __name__ == "__main__":
    app.run(debug=True)