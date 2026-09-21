from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = "nazifs-scents"

# Load products
with open("data/products.json", "r") as file:
    products = json.load(file)


@app.route("/")
def home():
    return render_template("index.html", products=products)


@app.route("/shop")
def shop():
    category = request.args.get("category", "All")

    if category == "All":
        filtered_products = products
    else:
        filtered_products = [
            p for p in products if p["category"] == category
        ]

    return render_template(
        "shop.html",
        products=filtered_products,
        category=category
    )


@app.route("/product/<int:product_id>")
def product(product_id):
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    return render_template(
        "product.html",
        product=product
    )


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


@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if request.method == "POST":
        session["cart"] = []

        return render_template(
            "checkout.html",
            complete=True
        )

    return render_template("checkout.html")


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)