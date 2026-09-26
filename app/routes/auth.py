import os
import secrets
from datetime import datetime, timedelta

import requests

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app import db
from app.models import User, RegistrationVerification


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

BREVO_SENDER_EMAIL = "jibojororahama@gmail.com"
BREVO_SENDER_NAME = "TransLink"


# ============================================================
# SEND VERIFICATION EMAIL WITH BREVO
# ============================================================

def send_verification_email(email, full_name, code):

    api_key = os.environ.get("BREVO_API_KEY")

    if not api_key:
        print("ERROR: BREVO_API_KEY is not configured.")
        return False

    payload = {
        "sender": {
            "name": BREVO_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL
        },

        "to": [
            {
                "email": email,
                "name": full_name
            }
        ],

        "subject": "TransLink Email Verification",

        "htmlContent": f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>TransLink Email Verification</title>
        </head>

        <body style="
            margin:0;
            padding:0;
            background:#f4f7fb;
            font-family:Arial, Helvetica, sans-serif;
        ">

            <div style="
                max-width:600px;
                margin:40px auto;
                background:#ffffff;
                border-radius:14px;
                padding:35px;
                box-shadow:0 5px 20px rgba(0,0,0,0.08);
            ">

                <h2 style="
                    margin-top:0;
                    color:#0d6efd;
                ">
                    TransLink Email Verification
                </h2>

                <p>
                    Hello <strong>{full_name}</strong>,
                </p>

                <p>
                    Thank you for registering with TransLink.
                    Please use the verification code below to
                    complete your registration.
                </p>

                <div style="
                    margin:30px 0;
                    padding:20px;
                    background:#f1f5ff;
                    border-radius:10px;
                    text-align:center;
                ">

                    <div style="
                        font-size:34px;
                        font-weight:bold;
                        letter-spacing:8px;
                        color:#0d6efd;
                    ">
                        {code}
                    </div>

                </div>

                <p>
                    This verification code will expire in
                    <strong>10 minutes</strong>.
                </p>

                <p>
                    If you did not create a TransLink account,
                    you can safely ignore this email.
                </p>

                <hr style="
                    border:none;
                    border-top:1px solid #eeeeee;
                    margin:30px 0;
                ">

                <p style="
                    font-size:13px;
                    color:#777777;
                ">
                    TransLink<br>
                    Connecting Truck Owners with Traders
                </p>

            </div>

        </body>
        </html>
        """
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    try:

        response = requests.post(
            BREVO_API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )

        print("Brevo status:", response.status_code)
        print("Brevo response:", response.text)

        if response.status_code == 201:
            return True

        return False

    except requests.RequestException as error:

        print("Brevo request error:", error)

        return False


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        role = request.form.get(
            "role",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not full_name or not email or not phone or not role:

            flash(
                "Please complete all required fields.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        if role not in ["trader", "owner"]:

            flash(
                "Please select a valid account type.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "auth/register.html"
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists. "
                "Please login instead.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        old_verification = (
            RegistrationVerification.query
            .filter_by(email=email)
            .first()
        )

        if old_verification:

            db.session.delete(old_verification)
            db.session.commit()

        verification_code = (
            f"{secrets.randbelow(1000000):06d}"
        )

        verification = RegistrationVerification(

            full_name=full_name,

            email=email,

            phone=phone,

            role=role,

            password_hash=generate_password_hash(
                password
            ),

            code_hash=generate_password_hash(
                verification_code
            ),

            expires_at=(
                datetime.utcnow()
                + timedelta(minutes=10)
            ),

            attempts=0
        )

        db.session.add(verification)

        db.session.commit()

        session["pending_verification_id"] = (
            verification.id
        )

        email_sent = send_verification_email(
            email,
            full_name,
            verification_code
        )

        if not email_sent:

            db.session.delete(verification)
            db.session.commit()

            session.pop(
                "pending_verification_id",
                None
            )

            flash(
                "We could not send the verification code. "
                "Please try again later.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        flash(
            "A verification code has been sent to your email.",
            "success"
        )

        return redirect(
            url_for("auth.verify_email")
        )

    return render_template(
        "auth/register.html"
    )


# ============================================================
# VERIFY EMAIL
# ============================================================

@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():

    verification_id = session.get(
        "pending_verification_id"
    )

    if not verification_id:

        flash(
            "No pending email verification was found.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    verification = (
        RegistrationVerification.query
        .filter_by(id=verification_id)
        .first()
    )

    if not verification:

        session.pop(
            "pending_verification_id",
            None
        )

        flash(
            "Verification session has expired. "
            "Please register again.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    if datetime.utcnow() > verification.expires_at:

        db.session.delete(verification)
        db.session.commit()

        session.pop(
            "pending_verification_id",
            None
        )

        flash(
            "Your verification code has expired. "
            "Please register again.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip()

        if not code.isdigit() or len(code) != 6:

            flash(
                "Please enter the 6-digit verification code.",
                "danger"
            )

            return render_template(
                "auth/verify_email.html",
                email=verification.email
            )

        if verification.attempts >= 5:

            db.session.delete(verification)
            db.session.commit()

            session.pop(
                "pending_verification_id",
                None
            )

            flash(
                "Too many incorrect attempts. "
                "Please register again.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        verification.attempts += 1

        if not check_password_hash(
            verification.code_hash,
            code
        ):

            db.session.commit()

            remaining = (
                5 - verification.attempts
            )

            flash(
                f"Incorrect verification code. "
                f"{remaining} attempt(s) remaining.",
                "danger"
            )

            return render_template(
                "auth/verify_email.html",
                email=verification.email
            )

        existing_user = User.query.filter_by(
            email=verification.email
        ).first()

        if existing_user:

            db.session.delete(verification)
            db.session.commit()

            session.pop(
                "pending_verification_id",
                None
            )

            flash(
                "An account with this email already exists.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        user = User(

            full_name=verification.full_name,

            email=verification.email,

            phone=verification.phone,

            role=verification.role,

            password_hash=verification.password_hash,

            is_active=True
        )

        db.session.add(user)

        db.session.delete(verification)

        db.session.commit()

        session.clear()

        session["logged_in"] = True
        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.full_name
        session["user_email"] = user.email

        flash(
            "Email verified successfully. "
            "Your TransLink account has been created.",
            "success"
        )

        if user.role == "trader":

            return redirect(
                url_for("trader.dashboard")
            )

        if user.role == "owner":

            return redirect(
                url_for("owner.dashboard")
            )

        return redirect(
            url_for("main.home")
        )

    return render_template(
        "auth/verify_email.html",
        email=verification.email
    )


# ============================================================
# RESEND VERIFICATION CODE
# ============================================================

@auth_bp.route(
    "/resend-verification",
    methods=["POST"]
)
def resend_verification():

    verification_id = session.get(
        "pending_verification_id"
    )

    if not verification_id:

        flash(
            "No pending verification was found.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    verification = (
        RegistrationVerification.query
        .filter_by(id=verification_id)
        .first()
    )

    if not verification:

        session.pop(
            "pending_verification_id",
            None
        )

        flash(
            "Verification session has expired.",
            "warning"
        )

        return redirect(
            url_for("auth.register")
        )

    verification_code = (
        f"{secrets.randbelow(1000000):06d}"
    )

    verification.code_hash = (
        generate_password_hash(
            verification_code
        )
    )

    verification.expires_at = (
        datetime.utcnow()
        + timedelta(minutes=10)
    )

    verification.attempts = 0

    db.session.commit()

    email_sent = send_verification_email(
        verification.email,
        verification.full_name,
        verification_code
    )

    if not email_sent:

        flash(
            "We could not resend the verification code. "
            "Please try again later.",
            "danger"
        )

        return redirect(
            url_for("auth.verify_email")
        )

    flash(
        "A new verification code has been sent.",
        "success"
    )

    return redirect(
        url_for("auth.verify_email")
    )


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        if not user.is_active:

            flash(
                "Your account has been deactivated.",
                "danger"
            )

            return render_template(
                "auth/login.html"
            )

        session.clear()

        session["logged_in"] = True
        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.full_name
        session["user_email"] = user.email

        flash(
            "Login successful.",
            "success"
        )

        if user.role == "admin":

            return redirect(
                url_for("admin.dashboard")
            )

        if user.role == "owner":

            return redirect(
                url_for("owner.dashboard")
            )

        return redirect(
            url_for("trader.dashboard")
        )

    return render_template(
        "auth/login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("main.home")
    )


# ============================================================
# TEMPORARY ADMIN PASSWORD RESET
# ============================================================
# IMPORTANT:
# This route is temporary.
# Remove it after recovering the admin account.
# ============================================================

@auth_bp.route("/admin-reset", methods=["GET", "POST"])
def admin_reset():

    admins = User.query.filter_by(
        role="admin"
    ).all()

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        new_password = request.form.get(
            "password",
            ""
        )

        if not email or not new_password:

            flash(
                "Email and password are required.",
                "danger"
            )

            return redirect(
                url_for("auth.admin_reset")
            )

        if len(new_password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("auth.admin_reset")
            )

        user = User.query.filter_by(
            email=email,
            role="admin"
        ).first()

        if not user:

            flash(
                "No administrator account was found with that email.",
                "danger"
            )

            return redirect(
                url_for("auth.admin_reset")
            )

        user.password_hash = generate_password_hash(
            new_password
        )

        user.is_active = True

        db.session.commit()

        flash(
            "Admin password has been reset successfully.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    admin_emails = [
        admin.email
        for admin in admins
    ]

    return render_template(
        "auth/admin_reset.html",
        admin_emails=admin_emails
    )