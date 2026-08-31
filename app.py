import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

app = Flask(__name__)
app.secret_key = "dms-assessment-key"

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "packages.json"
DATABASE = BASE_DIR / "dms.db"

DISCOUNT_RATE = 0.10
DISCOUNT_LIMIT = 2000
MAX_ADDONS = 4

ADDONS = {
    "social_media": {
        "name": "Social Media Starter Pack",
        "price": 199,
    },
    "google_profile": {
        "name": "Google Business Profile Setup",
        "price": 149,
    },
    "analytics": {
        "name": "Analytics Setup",
        "price": 99,
    },
    "extra_revision": {
        "name": "Extra Revision Round",
        "price": 75,
    },
}


def load_packages():
    """Load package data from the JSON file."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_packages(packages):
    """Save updated package data back to JSON."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(packages, file, indent=4)


def get_connection():
    """Create a connection to the SQLite database."""
    return sqlite3.connect(DATABASE)


def initialise_database():
    """Create the orders table if it does not exist."""
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            business_name TEXT NOT NULL,
            package_name TEXT NOT NULL,
            addons TEXT,
            subtotal REAL NOT NULL,
            discount REAL NOT NULL,
            total REAL NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def find_package(package_id):
    """Find one package using its ID."""
    for package in load_packages():
        if package["id"] == package_id:
            return package

    return None


def calculate_quote(package_id, selected_addons):
    """Calculate subtotal, discount and final price."""
    package = find_package(package_id)

    if package is None:
        return None

    addon_total = 0
    addon_names = []

    for addon_id in selected_addons:
        addon = ADDONS.get(addon_id)

        if addon is not None:
            addon_total += addon["price"]
            addon_names.append(addon["name"])

    subtotal = package["price"] + addon_total

    if subtotal >= DISCOUNT_LIMIT:
        discount = round(subtotal * DISCOUNT_RATE, 2)
    else:
        discount = 0

    total = round(subtotal - discount, 2)

    return {
        "package": package,
        "addon_names": addon_names,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
    }


def reduce_package_availability(package_id):
    """Reduce available package slots after a successful order."""
    packages = load_packages()

    for package in packages:
        if package["id"] == package_id:
            if package["availability"] <= 0:
                return False

            package["availability"] -= 1
            save_packages(packages)
            return True

    return False


def restore_package_availability(package_name):
    """Restore one package slot after cancelling an order."""
    packages = load_packages()

    for package in packages:
        if package["name"] == package_name:
            package["availability"] += 1
            save_packages(packages)
            return


def create_order(data):
    """Save a completed order to SQLite."""
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO orders (
            customer_name,
            email,
            business_name,
            package_name,
            addons,
            subtotal,
            discount,
            total,
            created_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )

    order_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return order_id


def get_orders():
    """Return saved orders from newest to oldest."""
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            customer_name,
            email,
            business_name,
            package_name,
            addons,
            subtotal,
            discount,
            total,
            created_at,
            status
        FROM orders
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return rows


def cancel_saved_order(order_id):
    """Cancel an active order and restore package availability."""
    connection = get_connection()

    row = connection.execute(
        """
        SELECT package_name, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    ).fetchone()

    if row is None or row[1] == "Cancelled":
        connection.close()
        return False

    connection.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        ("Cancelled", order_id),
    )

    connection.commit()
    connection.close()

    restore_package_availability(row[0])

    return True


def write_invoice(order_id, customer, quote):
    """Create a text invoice for the customer."""
    invoice_folder = BASE_DIR / "invoices"
    invoice_folder.mkdir(exist_ok=True)

    invoice_file = invoice_folder / f"DMS_Invoice_{order_id}.txt"

    lines = [
        "DIGITAL MARKETING SOLUTIONS",
        "--------------------------------",
        f"Invoice: DMS-{order_id:04d}",
        f"Date: {datetime.now():%d/%m/%Y %H:%M}",
        "",
        f"Customer: {customer['name']}",
        f"Business: {customer['business']}",
        f"Email: {customer['email']}",
        "",
        f"Package: {quote['package']['name']}",
        f"Package price: ${quote['package']['price']:.2f}",
        "",
        "Add-ons:",
    ]

    if quote["addon_names"]:
        for addon in quote["addon_names"]:
            lines.append(f"- {addon}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            f"Subtotal: ${quote['subtotal']:.2f}",
            f"Discount: -${quote['discount']:.2f}",
            f"Total: ${quote['total']:.2f}",
            "",
            "Thank you for choosing DMS.",
        ]
    )

    invoice_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


@app.route("/")
def home():
    """Display the DMS homepage."""
    return render_template(
        "index.html",
        packages=load_packages(),
        addons=ADDONS,
    )


@app.route("/services")
def services():
    """Display DMS services."""
    return render_template("services.html")


@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/packages")
def packages():
    """Display packages and the quote builder."""
    return render_template(
        "packages.html",
        packages=load_packages(),
        addons=ADDONS,
        discount_limit=DISCOUNT_LIMIT,
        discount_rate=DISCOUNT_RATE,
    )


@app.route("/create_order", methods=["POST"])
def create_order_route():
    """Validate customer input and create an order."""
    name = request.form.get("customer_name", "").strip()
    email = request.form.get("email", "").strip()
    business = request.form.get("business_name", "").strip()
    package_id = request.form.get("package_id", "").strip()
    selected_addons = request.form.getlist("addons")

    if not name or not email or not business:
        flash("Please complete all customer details.")
        return redirect(url_for("packages"))

    if "@" not in email or "." not in email:
        flash("Please enter a valid email address.")
        return redirect(url_for("packages"))

    if len(selected_addons) > MAX_ADDONS:
        flash("You can select a maximum of four add-ons.")
        return redirect(url_for("packages"))

    quote = calculate_quote(
        package_id,
        selected_addons,
    )

    if quote is None:
        flash("Please select a valid package.")
        return redirect(url_for("packages"))

    if quote["package"]["availability"] <= 0:
        flash("That package is currently unavailable.")
        return redirect(url_for("packages"))

    if not reduce_package_availability(package_id):
        flash("The package is no longer available.")
        return redirect(url_for("packages"))

    customer = {
        "name": name,
        "email": email,
        "business": business,
    }

    addon_text = ", ".join(
        quote["addon_names"]
    ) or "None"

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    data = (
        name,
        email,
        business,
        quote["package"]["name"],
        addon_text,
        quote["subtotal"],
        quote["discount"],
        quote["total"],
        created_at,
        "Active",
    )

    order_id = create_order(data)

    write_invoice(
        order_id,
        customer,
        quote,
    )

    return render_template(
        "invoice.html",
        order_id=order_id,
        customer=customer,
        quote=quote,
    )


@app.route("/orders")
def orders():
    """Display saved customer orders."""
    return render_template(
        "order_history.html",
        orders=get_orders(),
    )


@app.route(
    "/cancel_order/<int:order_id>",
    methods=["POST"],
)
def cancel_order_route(order_id):
    """Cancel a saved customer order."""
    changed = cancel_saved_order(order_id)

    if changed:
        flash(
            f"Order DMS-{order_id:04d} has been cancelled."
        )
    else:
        flash("Order could not be found or was already cancelled.")

    return redirect(url_for("orders"))


@app.errorhandler(404)
def page_not_found(error):
    """Display a friendly 404 message."""
    return (
        "DMS - Page not found. "
        "Please return to the homepage.",
        404,
    )


initialise_database()


if __name__ == "__main__":
    app.run(debug=True)