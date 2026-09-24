from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from app import db
from app.models import Notification


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


@notifications_bp.route("/")
def index():

    if "user_id" not in session:
        flash("Please login to view your notifications.", "warning")
        return redirect(url_for("auth.login"))

    notifications = (
        Notification.query
        .filter_by(user_id=session["user_id"])
        .order_by(Notification.created_at.desc())
        .all()
    )

    unread_count = Notification.query.filter_by(
        user_id=session["user_id"],
        is_read=False
    ).count()

    return render_template(
        "notifications/index.html",
        notifications=notifications,
        unread_count=unread_count
    )


@notifications_bp.route("/read/<int:notification_id>", methods=["POST"])
def mark_read(notification_id):

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=session["user_id"]
    ).first_or_404()

    notification.is_read = True

    db.session.commit()

    return redirect(url_for("notifications.index"))


@notifications_bp.route("/read-all", methods=["POST"])
def mark_all_read():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

    Notification.query.filter_by(
        user_id=session["user_id"],
        is_read=False
    ).update(
        {"is_read": True},
        synchronize_session=False
    )

    db.session.commit()

    flash("All notifications marked as read.", "success")

    return redirect(url_for("notifications.index"))