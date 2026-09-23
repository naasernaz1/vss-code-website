from flask import Flask, render_template, redirect, url_for, session, request
from datetime import datetime
from collections import Counter
import json
import os


app = Flask(__name__)
app.secret_key = "nazifs-scents-secret"


# =========================================================
# PRODUCTS
# =========================================================

with open("data/products.json", "r", encoding="utf-8") as file:
    products = json.load(file)


# =========================================================
# INVOICE FUNCTIONS
# =========================================================

INVOICE_FILE = "data/invoices.json"


def load_invoices():

    # If invoices.json does not exist yet
    if not os.path.exists(INVOICE_FILE):
        return []

    try:
        with open(INVOICE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        return []


def save_invoices(invoices):

    with open(INVOICE_FILE, "w", encoding="utf-8") as file:
        json.dump(invoices, file, indent=4)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# SHOP - ALL PRODUCTS
# =========================================================

@app.route("/shop")
def shop():

    return render_template(
        "shop.html",
        products=products,
        category="All",
        page_title="Shop fragrances",
        page_subtitle="Find your next signature scent."
    )


# =========================================================
# MEN'S PRODUCTS
# =========================================================

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


# =========================================================
# WOMEN'S PRODUCTS
# =========================================================

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


# =========================================================
# INDIVIDUAL PRODUCT PAGE
# =========================================================

@app.route("/product/<int:product_id>")
def product(product_id):

    item = next(
        (
            p for p in products
            if p["id"] == product_id
        ),
        None
    )

    if item is None:
        return "Product not found", 404

    return render_template(
        "products.html",
        product=item
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route("/add/<int:product_id>")
def add_to_cart(product_id):

    item = next(
        (
            p for p in products
            if p["id"] == product_id
        ),
        None
    )

    if item is None:
        return "Product not found", 404

    cart = session.get("cart", [])

    cart.append(product_id)

    session["cart"] = cart

    return redirect(
        url_for("cart")
    )


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    cart_ids = session.get("cart", [])

    cart_products = []

    for product_id in cart_ids:

        item = next(
            (
                p for p in products
                if p["id"] == product_id
            ),
            None
        )

        if item is not None:
            cart_products.append(item)

    total = sum(
        product["price"]
        for product in cart_products
    )

    return render_template(
        "cart.html",
        products=cart_products,
        total=total
    )


# =========================================================
# CHECKOUT
# =========================================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart_ids = session.get("cart", [])

    # Stop checkout if cart is empty
    if not cart_ids:
        return redirect(
            url_for("cart")
        )


    # Count how many of each product is in cart
    product_counts = Counter(cart_ids)

    checkout_products = []


    for product_id, quantity in product_counts.items():

        item = next(
            (
                p for p in products
                if p["id"] == product_id
            ),
            None
        )

        if item is not None:

            checkout_products.append({
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": quantity,
                "line_total": item["price"] * quantity
            })


    total = sum(
        item["line_total"]
        for item in checkout_products
    )


    # =====================================================
    # WHEN CUSTOMER PRESSES PLACE ORDER
    # =====================================================

    if request.method == "POST":

        customer_name = request.form.get(
            "name",
            ""
        ).strip()

        customer_email = request.form.get(
            "email",
            ""
        ).strip()

        customer_address = request.form.get(
            "address",
            ""
        ).strip()


        # Basic validation
        if not customer_name or not customer_email or not customer_address:

            return render_template(
                "checkout.html",
                products=checkout_products,
                total=total,
                error="Please complete all customer details."
            )


        # Create invoice number
        invoice_number = (
            "INV-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
        )


        # Create invoice
        invoice = {

            "invoice_number": invoice_number,

            "date": datetime.now().strftime(
                "%d/%m/%Y"
            ),

            "customer_name": customer_name,

            "customer_email": customer_email,

            "customer_address": customer_address,

            "items": checkout_products,

            "total": total
        }


        # Save invoice
        invoices = load_invoices()

        invoices.append(invoice)

        save_invoices(invoices)


        # Clear shopping cart
        session["cart"] = []


        # Take customer to their invoice
        return redirect(
            url_for(
                "view_invoice",
                invoice_number=invoice_number
            )
        )


    # Normal checkout page
    return render_template(
        "checkout.html",
        products=checkout_products,
        total=total
    )


# =========================================================
# VIEW A SINGLE INVOICE
# =========================================================

@app.route("/invoice/<invoice_number>")
def view_invoice(invoice_number):

    invoices = load_invoices()

    invoice = next(
        (
            invoice
            for invoice in invoices
            if invoice["invoice_number"]
            == invoice_number
        ),
        None
    )


    if invoice is None:
        return "Invoice not found", 404


    return render_template(
        "invoice.html",
        invoice=invoice
    )


# =========================================================
# VIEW ALL INVOICES
# =========================================================

@app.route("/invoices")
def invoices():

    invoice_list = load_invoices()

    # Newest invoices first
    invoice_list.reverse()

    return render_template(
        "invoices.html",
        invoices=invoice_list
    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():

    return render_template(
        "services.html"
    )


# =========================================================
# PACKAGES
# =========================================================

@app.route("/packages")
def packages():

    return render_template(
        "packages.html"
    )


# =========================================================
# ORDER HISTORY
# =========================================================

@app.route("/order-history")
def order_history():

    return render_template(
        "order_history.html"
    )


# =========================================================
# RUN WEBSITE
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)