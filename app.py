import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date

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
    # Get user ID  and username
    user_id = session.get("user_id")
    username = db.execute(
        "SELECT username FROM users WHERE id = :uid", uid=user_id)[0]["username"]
    # Get current user cash
    user_cash = db.execute(
        "SELECT cash FROM users WHERE id = :uid", uid=user_id)[0]["cash"]
    # Get current owned shares
    user_assets = db.execute(
        "SELECT symbol, name, SUM(shares) FROM transactions WHERE userID = :uid GROUP BY symbol ORDER BY symbol", uid=user_id)
    # Initiate the total sum of user's cash and the value of all the assets
    total_assets = user_cash

    # If shares are more than 0, display their stock and add their value to the total cash
    for asset in user_assets:
        if asset["SUM(shares)"] > 0:
            stock_info = lookup(asset["symbol"])
            asset["price"] = usd(stock_info["price"])
            asset["total_cost"] = usd(
                asset["SUM(shares)"] * stock_info["price"])
            total_assets = total_assets + \
                (asset["SUM(shares)"] * stock_info["price"])

    return render_template("index.html", user=username, assets=user_assets, cash=usd(user_cash), total_assets=usd(total_assets))


"""
Buy shares of stock
============================================
"""


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    user_id = session.get("user_id")

    if request.method == "POST":
        symbol = request.form.get("symbol")
        # If no value provided
        if not symbol:
            return apology('', 'please enter a valid symbol')

        stock_info = lookup(symbol)
        # If symbol is unavailable or invalid
        if stock_info is None:
            return apology('', 'No such symbol')
        else:
            shares = int(request.form.get("shares"))
            total_cost = shares * stock_info["price"]
            user_cash = db.execute(
                "SELECT cash FROM users WHERE id = :uid", uid=user_id)[0]["cash"]
            # Ensure user has enough cash
            if user_cash < total_cost:
                return apology("not enough money", "pooooor!")
            else:
                # save transaction in db with its datetime
                now = datetime.now()
                db.execute(
                    "INSERT INTO transactions (userID, symbol, name, shares, unit_price, total_cost, dateID) VALUES (:userID, :symbol, :name, :shares, :unit_price, :total_cost, :dateID)",
                    userID=user_id,
                    symbol=stock_info["symbol"],
                    name=stock_info["name"],
                    shares=shares,
                    unit_price=stock_info["price"],
                    total_cost=total_cost,
                    dateID=now
                )
                # calculate the remainder of the user's cash
                rest = user_cash - total_cost
                db.execute("UPDATE users SET cash = :rest WHERE id = :uid",
                           rest=rest, uid=user_id)
                # Flash a msg when the transaction succeeds, depending on the amount of money left
                if rest == 0:
                    flash("No more cash!")
                elif rest < 5:
                    flash("You just milked off your account.")
                else:
                    flash("Successful Process!")
            return redirect("/")

    # If method = GET
    else:
        username = db.execute(
            "SELECT username FROM users WHERE id = :uid", uid=user_id)[0]["username"]
        return render_template("buy.html", user=username)


"""
Show history of transactions
============================================
"""


@app.route("/history")
@login_required
def history():
    user_id = session.get("user_id")
    username = db.execute(
        "SELECT username FROM users WHERE id = :uid", uid=user_id)[0]["username"]

    # Get all transactions by this user
    transactions = db.execute(
        "SELECT symbol, shares, unit_price, dateID FROM transactions WHERE userID = :uid ORDER BY dateID DESC", uid=user_id)
    # Change date format
    for transaction in transactions:
        parsed_date = datetime.strptime(
            transaction["dateID"], "%Y-%m-%d %H:%M:%S")
        transaction["dateID"] = parsed_date.strftime("%H:%M %p on %d %b, %Y")
    # Ensure user has previous transactions or else apologize
    if len(transactions) is 0:
        return apology(" made yet", "No transactions")
    return render_template("history.html", user=username, transactions=transactions)


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
    user_id = session.get("user_id")
    username = db.execute(
        "SELECT username FROM users WHERE id = :uid", uid=user_id)[0]["username"]
    if request.method == "POST":
        # Ensure symbol is valid
        stock_info = lookup(request.form.get("symbol"))
        if not stock_info:
            return apology("", "No such stock")
        else:
            # If user own shares of this stock, show sell button on quote.html
            owned_shares = db.execute(
                "SELECT SUM(shares) FROM transactions WHERE userID = :uid AND symbol = :symbol GROUP BY symbol",
                uid=user_id, symbol=stock_info['symbol']
            )
            ownShares = False
            if len(owned_shares) == 1 and owned_shares[0]["SUM(shares)"] > 0:
                ownShares = True

            return render_template(
                "quote.html",
                showResult=True,
                name=stock_info['name'],
                symbol=stock_info['symbol'],
                price=stock_info['price'],
                ownShares=ownShares,
                user=username
            )
    else:
        return render_template("quote.html", user=username)


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
        # Ensure username length is at max 10 chracters
        if not len(request.form.get("username")) <= 10:
            return apology("max 10 characters", "long username")
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
    user_id = session.get("user_id")

    if request.method == "POST":
        symbol = request.form.get("symbol")
        # If no value provided
        if not symbol:
            return apology('', 'please enter a valid symbol')

        stock_info = lookup(symbol)
        # If symbol is unavailable or invalid
        if stock_info is None:
            return apology('', 'No such symbol')
        else:
            shares_to_sell = int(request.form.get("shares"))
            owned_shares = db.execute(
                "SELECT SUM(shares) FROM transactions WHERE userID = :uid AND symbol = :symbol", uid=user_id, symbol=symbol)[0]["SUM(shares)"]
            # Ensure number of shares to sell is enough and valid
            if shares_to_sell > owned_shares:
                return apology("You don't own that much", "Scammer")
            elif shares_to_sell < 0:
                return apology("Invalid number of shares", "try again")

            total_cost = shares_to_sell * stock_info["price"]
            user_cash = db.execute(
                "SELECT cash FROM users WHERE id = :uid", uid=user_id)[0]["cash"]
            # Save transaction in db, with a negative number of shares indicating selling
            now = datetime.now()
            db.execute(
                "INSERT INTO transactions (userID, symbol, name, shares, unit_price, total_cost, dateID) VALUES (:userID, :symbol, :name, :shares, :unit_price, :total_cost, :dateID)",
                userID=user_id,
                symbol=stock_info["symbol"],
                name=stock_info["name"],
                shares=shares_to_sell-(shares_to_sell*2),
                unit_price=stock_info["price"],
                total_cost=total_cost,
                dateID=now
            )

            # Adding money for sold shares to user cash balance
            new_cash = user_cash + total_cost
            db.execute(
                "UPDATE users SET cash = :new_cash WHERE id = :uid",
                new_cash=new_cash, uid=user_id
            )
            flash("Successful Process!")
            return redirect("/")

    # If method = GET
    else:
        # Get symbols whose sum of shares more than zero to be displayed in select menu
        db_symbols = db.execute(
            "SELECT symbol, SUM(shares) FROM transactions WHERE userID = :uid GROUP BY symbol", uid=user_id)
        symbols = []
        for symbol in db_symbols:
            if symbol["SUM(shares)"] > 0:
                symbols.append(symbol["symbol"])
        username = db.execute(
            "SELECT username FROM users WHERE id = :uid", uid=user_id)[0]["username"]
        return render_template("sell.html", user=username, symbols=symbols)


"""
Change Password
============================================
"""


@app.route("/change_pw", methods=["GET", "POST"])
def change_pw():
    user_id = session.get("user_id")

    if request.method == "POST":
        # Ensure current password was submitted
        if not request.form.get("old-password"):
            return apology("Incorrect password", 403)
        # Ensure a new password is provided
        elif not request.form.get("new-password"):
            return apology("must provide password", 403)
        # Ensure both new password entries match
        elif not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("new-password"):
            return apology("New passwords don't match", 403)
        #  Ensure current password matches the db
        old_password = db.execute(
            "SELECT hash FROM users WHERE id = :uid", uid=user_id)[0]["hash"]
        if not check_password_hash(old_password, request.form.get("old-password")):
            return apology("Incorrect password", 403)

        # Change password in db
        db.execute("UPDATE users SET hash = :new_hash WHERE id = :uid",
                   uid=user_id, new_hash=generate_password_hash(request.form.get("new-password")))
        flash('Password changed successfully')
        return redirect("/")

    # If method = GET
    else:
        username = db.execute(
            "SELECT username FROM users WHERE id = :uid", uid=user_id
        )[0]["username"]
        return render_template("change_pw.html", user=username)


"""
Add funds
============================================
"""


@app.route("/add_funds", methods=["GET", "POST"])
def add_funds():
    user_id = session.get("user_id")

    if request.method == "POST":
        # Ensure a value is provided
        if not request.form.get("funds"):
            return apology("Must enter value", 403)

        funds = int(request.form.get("funds"))
        # Ensure amount is between 100 and 1000
        if funds > 1000 or funds < 100:
            return apology("Invalid Amount", 403)
        # Add funds
        else:
            current_cash = db.execute(
                "SELECT cash FROM users WHERE id = :uid", uid=user_id)[0]["cash"]
            today = date.today()
            db.execute(
                "INSERT INTO funds (userID, cash_before, amount, dateID) VALUES (:uid, :cash_before, :amount, :dateID)",
                uid=user_id, cash_before=current_cash, amount=funds, dateID=today
            )
            db.execute("UPDATE users SET cash = :new_cash WHERE id = :uid",
                       new_cash=current_cash+funds, uid=user_id)
            flash("Funds were added successfully!")
            return redirect("/")
    # If method = GET
    else:
        # Retrieve previous processes, if any
        previous_funds = db.execute(
            "SELECT amount, dateID FROM funds WHERE userID = :uid ORDER BY dateID DESC LIMIT 5", uid=user_id)

        funded_today = False
        if len(previous_funds) > 0:
            # Check if user already added funds for the day
            today = date.today().strftime("%Y-%m-%d")
            if previous_funds[0]["dateID"] == today:
                funded_today = True
            # Change date format
            for fund in previous_funds:
                parsed_date = datetime.strptime(fund["dateID"], "%Y-%m-%d")
                fund["dateID"] = parsed_date.strftime("%d %b, %Y")
        elif len(previous_funds) == 0:
            previous_funds = None
        username = db.execute(
            "SELECT username FROM users WHERE id = :uid", uid=user_id
        )[0]["username"]
        return render_template("add_funds.html", user=username, funded_today=funded_today, funds=previous_funds)


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
