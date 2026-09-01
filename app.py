from flask import Flask, render_template

app = Flask(__name__)

products = [
    ["Oud Noir", 129],
    ["Vanilla Mist", 119],
    ["Midnight Rose", 129],
    ["Amber Gold", 139],
    ["Ocean Blue", 119]
]

@app.route("/")
def home():
    return render_template("index.html", products=products)

app.run(debug=True)