import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

"""
Show portfolio of stocks
============================================
"""


@app.route("/")
@login_required
def index():
    return render_template("index.html")


"""
Buy shares of stock
============================================
"""


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # If no value provided
        if not symbol:
            return apology('', 'please enter a valid symbol')

        stock_pack = lookup(symbol)
        # If symbol is unavailable or invalid
        if stock_pack is None:
            return apology('', 'No such symbol')
        else:
            user_id = session.get("user_id")
            shares = int(request.form.get("shares"))
            total_cost = shares * stock_pack["price"]
            user_cash = db.execute(
                "SELECT cash FROM users WHERE id = :uid", uid=user_id)

            if len(user_cash) != 1:
                return apology(len(user_cash), "db array sucks")
            elif user_cash[0]["cash"] < total_cost:
                return apology("pooooor!", "not enough money")
            else:
                now = datetime.now()
                db.execute(
                    "INSERT INTO stock (userID, symbol, name, shares, unit_price, total_cost, dateID) VALUES (:userID, :symbol, :name, :shares, :unit_price, :total_cost, :dateID)",
                    userID=user_id,
                    symbol=stock_pack["symbol"],
                    name=stock_pack["name"],
                    shares=shares,
                    unit_price=stock_pack["price"],
                    total_cost=total_cost,
                    dateID=now
                )
                rest = user_cash[0]["cash"] - total_cost
                db.execute("UPDATE users SET cash = :rest WHERE id = :uid",
                           rest=rest, uid=user_id)
                if rest == 0:
                    flash("No more cash!")
                elif rest < 5:
                    flash("You just milked off your account.")
                else:
                    flash("Successful Process!")
            return render_template("index.html")

    # If method = GET
    else:
        return render_template("buy.html")


"""
Show history of transactions
============================================
"""


@app.route("/history")
@login_required
def history():
    return apology("TODO")


"""
Log user in
============================================
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


"""
Log user out
============================================
"""


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


"""
Get stock quote.
============================================
"""


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        resp = lookup(request.form.get("symbol"))
        if not resp:
            return apology("", "No such stock")
        else:
            ownShares = False
            return render_template("quote.html", showResult=True, name=resp['name'], symbol=resp['symbol'], price=resp['price'], ownShares=ownShares)
    else:
        return render_template("quote.html")


"""
Register a new user
============================================
"""


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Ensure both password entries match
        elif not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords don't match", 403)

        # Query database for duplicate username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Reject registration if username is already in database
        if len(rows) > 0:
            return apology("TAKEN!", "Username")

        # If username is available: register user, then log in
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
        flash('Registered successfully! Log in below to access your account.')
        return render_template("login.html")

    # If method = GET
    else:
        return render_template("register.html")


"""
Sell shares of stock
============================================
"""


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    return apology("TODO")


"""
Handle error
============================================
"""


def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
