from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["MONGO_URI"] = "mongodb://localhost:27017/pgsystem"
mongo = PyMongo(app)

# ---------------- Initialize 100 rooms if not exist ----------------
if mongo.db.rooms.count_documents({}) == 0:
    for i in range(1, 101):
        mongo.db.rooms.insert_one({
            "room_id": i,
            "name": f"Room {i}",
            "price": 3000 + (i * 10),
            "rating": (i % 5) + 1,
            "image": f"{(i % 8) + 1}.jpeg",
            "booked": False,
            "booked_by": None,
            "booked_at": None,
            "booking_date": None
        })

# ---------------- Register / Login / Logout ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("⚠️ Fill all fields!", "danger")
            return redirect(url_for("register"))
        if mongo.db.users.find_one({"username": username}):
            flash("⚠️ Username already exists!", "danger")
            return redirect(url_for("register"))
        mongo.db.users.insert_one({"username": username, "password": password})
        flash("✅ Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("⚠️ Fill all fields!", "danger")
            return redirect(url_for("login"))
        user = mongo.db.users.find_one({"username": username})
        if user and user["password"] == password:
            session["user"] = username
            flash("✅ Login successful!", "success")
            return redirect(url_for("dashboard"))
        flash("❌ Invalid username or password", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for("login"))

# ---------------- Profile ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        flash("⚠️ Please login first.", "danger")
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"username": session["user"]})

    if request.method == "POST":
        new_name = request.form.get("name")
        new_mobile = request.form.get("mobile")
        new_email = request.form.get("email")

        mongo.db.users.update_one(
            {"username": session["user"]},
            {"$set": {
                "name": new_name,
                "mobile": new_mobile,
                "email": new_email
            }}
        )
        flash("✅ Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("⚠️ Please login first.", "danger")
        return redirect(url_for("login"))

    total_rooms = mongo.db.rooms.count_documents({})
    booked_rooms = mongo.db.rooms.count_documents({"booked": True})
    available_rooms = total_rooms - booked_rooms
    total_profit = sum([room["price"] for room in mongo.db.rooms.find({"booked": True})])

    user_rooms = list(mongo.db.rooms.find({"booked_by": session["user"]}))

    # Booking count per user
    users_booking = mongo.db.rooms.aggregate([
        {"$match": {"booked": True}},
        {"$group": {"_id": "$booked_by", "count": {"$sum": 1}}}
    ])

    return render_template(
        "dashboard.html",
        username=session["user"],
        total_rooms=total_rooms,
        booked_rooms=booked_rooms,
        available_rooms=available_rooms,
        total_profit=total_profit,
        user_rooms=user_rooms,
        users_booking=list(users_booking)
    )

# ---------------- Home / Rooms ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        flash("⚠️ Please login first.", "danger")
        return redirect(url_for("login"))

    page = int(request.args.get("page", 1))
    per_page = 20

    # Filter params
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    min_rating = request.args.get("min_rating")
    search_query = request.args.get("q", "")

    query = {}

    # Search by room name
    if search_query:
        query["name"] = {"$regex": search_query, "$options": "i"}

    # Filters
    if min_price:
        query.setdefault("price", {})
        query["price"]["$gte"] = int(min_price)
    if max_price:
        query.setdefault("price", {})
        query["price"]["$lte"] = int(max_price)
    if min_rating:
        query["rating"] = {"$gte": int(min_rating)}

    # Booking POST
    if request.method == "POST":
        room_id = int(request.form.get("room_id"))
        booking_date = request.form.get("booking_date")
        mongo.db.rooms.update_one(
            {"room_id": room_id},
            {"$set": {
                "booked": True,
                "booked_by": session.get("user"),
                "booked_at": datetime.now(),
                "booking_date": booking_date
            }}
        )
        flash(f"Room {room_id} booked for {booking_date}!", "success")
        return redirect(url_for("index", page=page, min_price=min_price, max_price=max_price, min_rating=min_rating, q=search_query))

    total_rooms = mongo.db.rooms.count_documents(query)
    rooms = list(mongo.db.rooms.find(query).skip((page - 1) * per_page).limit(per_page))
    available = mongo.db.rooms.count_documents({**query, "booked": False})
    total_pages = (total_rooms + per_page - 1) // per_page

    return render_template(
        "index.html",
        rooms=rooms,
        total=total_rooms,
        available=available,
        page=page,
        total_pages=total_pages,
        min_price=min_price or "",
        max_price=max_price or "",
        min_rating=min_rating or "",
        q=search_query
    )

# ---------------- Cancel Booking ----------------
@app.route("/cancel/<int:room_id>")
def cancel_booking(room_id):
    if "user" not in session:
        flash("⚠️ Please login first.", "danger")
        return redirect(url_for("login"))
    mongo.db.rooms.update_one(
        {"room_id": room_id},
        {"$set": {"booked": False, "booked_by": None, "booked_at": None, "booking_date": None}}
    )
    flash(f"Booking for Room {room_id} canceled!", "info")
    return redirect(request.referrer or url_for("index"))

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)