from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not full_name or not email or not phone or not role or not password:
            flash("Please complete all required fields.", "danger")
            return render_template("auth/register.html")

        if role not in ["trader", "owner"]:
            flash("Please select a valid account type.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        # Check existing email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "warning")
            return render_template("auth/register.html")

        # Create user
        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            phone=phone,
            is_active=True
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. You can now log in.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Your account has been deactivated. Contact the administrator.", "danger")
            return render_template("auth/login.html")

        # Create login session
        session.clear()

        session["user_id"] = user.id
        session["user_name"] = user.full_name
        session["user_role"] = user.role
        session["logged_in"] = True

        flash(f"Welcome back, {user.full_name}!", "success")

        # Role-based dashboard
        if user.role == "trader":
            return redirect(url_for("trader.dashboard"))

        elif user.role == "owner":
            return redirect(url_for("owner.dashboard"))

        elif user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("main.home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for("main.home"))