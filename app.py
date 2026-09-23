from flask import Flask, render_template, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = "nazifs-scents-secret"

with open("data/products.json", "r", encoding="utf-8") as file:
    products = json.load(file)


@app.route("/")
def home():
    return render_template("index.html", products=products)


@app.route("/shop")
def shop():
    category = "All"
    shown_products = products

    if category == "Men's":
        shown_products = [
            p for p in products if p["category"] == "Men's"
        ]

    return render_template(
        "shop.html",
        products=shown_products,
        category=category
    )


@app.route("/men")
def men():
    shown_products = [
        p for p in products if p["category"] == "Men's"
    ]

    return render_template(
        "shop.html",
        products=shown_products,
        category="Men's"
    )


@app.route("/women")
def women():
    shown_products = [
        p for p in products if p["category"] == "Women's"
    ]

    return render_template(
        "shop.html",
        products=shown_products,
        category="Women's"
    )


@app.route("/product/<int:product_id>")
def product(product_id):
    item = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if item is None:
        return "Product not found", 404

    return render_template("products.html", product=item)


@app.route("/add/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", [])
    cart.append(product_id)
    session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_ids = session.get("cart", [])

    cart_products = [
        p for p in products if p["id"] in cart_ids
    ]

    total = sum(p["price"] for p in cart_products)

    return render_template(
        "cart.html",
        products=cart_products,
        total=total
    )


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/packages")
def packages():
    return render_template("packages.html")


@app.route("/invoices")
def invoices():
    return render_template("invoices.html")


@app.route("/order-history")
def order_history():
    return render_template("order_history.html")


if __name__ == "__main__":
    app.run(debug=True)