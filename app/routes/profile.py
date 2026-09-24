from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile"
)


def login_required():
    return session.get("logged_in") is True


@profile_bp.route("/")
def index():
    if not login_required():
        flash("Please login to view your profile.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])

    return render_template(
        "profile/index.html",
        user=user
    )


@profile_bp.route("/edit", methods=["GET", "POST"])
def edit():
    if not login_required():
        flash("Please login to edit your profile.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(session["user_id"])

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

        if not full_name or not email or not phone:
            flash(
                "Please complete all required fields.",
                "danger"
            )

            return render_template(
                "profile/edit.html",
                user=user
            )

        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:
            flash(
                "That email address is already being used.",
                "danger"
            )

            return render_template(
                "profile/edit.html",
                user=user
            )

        user.full_name = full_name
        user.email = email
        user.phone = phone

        db.session.commit()

        session["user_name"] = user.full_name

        flash(
            "Your profile has been updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile.index")
        )

    return render_template(
        "profile/edit.html",
        user=user
    )


@profile_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if not login_required():
        flash(
            "Please login to change your password.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    user = User.query.get_or_404(
        session["user_id"]
    )

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not current_password:
            flash(
                "Enter your current password.",
                "danger"
            )

            return render_template(
                "profile/change_password.html"
            )

        if not check_password_hash(
            user.password_hash,
            current_password
        ):
            flash(
                "Your current password is incorrect.",
                "danger"
            )

            return render_template(
                "profile/change_password.html"
            )

        if len(new_password) < 6:
            flash(
                "Your new password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "profile/change_password.html"
            )

        if new_password != confirm_password:
            flash(
                "The new passwords do not match.",
                "danger"
            )

            return render_template(
                "profile/change_password.html"
            )

        user.password_hash = generate_password_hash(
            new_password
        )

        db.session.commit()

        flash(
            "Your password has been changed successfully.",
            "success"
        )

        return redirect(
            url_for("profile.index")
        )

    return render_template(
        "profile/change_password.html"
    )