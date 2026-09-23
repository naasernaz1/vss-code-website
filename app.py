from flask import Flask, render_template, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = "nazifs-scents-secret"


# Load products from JSON file
with open("data/products.json", "r", encoding="utf-8") as file:
    products = json.load(file)


# --------------------
# HOME PAGE
# --------------------

@app.route("/")
def home():
    return render_template("index.html", products=products)


# --------------------
# SHOP PAGE - ALL PRODUCTS
# --------------------

@app.route("/shop")
def shop():
    return render_template(
        "shop.html",
        products=products,
        category="All",
        page_title="Shop fragrances",
        page_subtitle="Find your next signature scent."
    )


# --------------------
# MEN'S PRODUCTS
# --------------------

@app.route("/men")
def men():
    shown_products = [
        p for p in products
        if p["category"] == "Men's"
    ]

    return render_template(
        "shop.html",
        products=shown_products,
        category="Men's",
        page_title="Men's fragrances",
        page_subtitle="Explore our fragrances for men."
    )


# --------------------
# WOMEN'S PRODUCTS
# --------------------

@app.route("/women")
def women():
    shown_products = [
        p for p in products
        if p["category"] == "Women's"
    ]

    return render_template(
        "shop.html",
        products=shown_products,
        category="Women's",
        page_title="Women's fragrances",
        page_subtitle="Explore our fragrances for women."
    )


# --------------------
# INDIVIDUAL PRODUCT PAGE
# --------------------

@app.route("/product/<int:product_id>")
def product(product_id):

    item = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if item is None:
        return "Product not found", 404

    return render_template(
        "products.html",
        product=item
    )


# --------------------
# ADD PRODUCT TO CART
# --------------------

@app.route("/add/<int:product_id>")
def add_to_cart(product_id):

    # Make sure the product actually exists
    item = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if item is None:
        return "Product not found", 404

    cart = session.get("cart", [])

    cart.append(product_id)

    session["cart"] = cart

    return redirect(url_for("cart"))


# --------------------
# CART
# --------------------

@app.route("/cart")
def cart():

    cart_ids = session.get("cart", [])

    cart_products = []

    # This allows the same product to appear more than once
    # if it has been added more than once.
    for product_id in cart_ids:

        item = next(
            (p for p in products if p["id"] == product_id),
            None
        )

        if item is not None:
            cart_products.append(item)

    total = sum(
        p["price"] for p in cart_products
    )

    return render_template(
        "cart.html",
        products=cart_products,
        total=total
    )


# --------------------
# CHECKOUT
# --------------------

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


# --------------------
# ABOUT
# --------------------

@app.route("/about")
def about():
    return render_template("about.html")


# --------------------
# OTHER PAGES
# --------------------

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


# --------------------
# RUN WEBSITE
# --------------------

if __name__ == "__main__":
    app.run(debug=True)