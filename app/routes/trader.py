from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from app import db
from app.models import TransportRequest, Booking


trader_bp = Blueprint(
    "trader",
    __name__,
    url_prefix="/trader"
)


@trader_bp.route("/")
def dashboard():

    if not session.get("logged_in"):
        flash("Please login to access your dashboard.", "warning")
        return redirect(url_for("auth.login"))

    if session.get("user_role") != "trader":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("main.home"))

    trader_id = session.get("user_id")

    requests = TransportRequest.query.filter_by(
        trader_id=trader_id
    ).order_by(
        TransportRequest.created_at.desc()
    ).all()

    total_requests = len(requests)

    pending_requests = TransportRequest.query.filter_by(
        trader_id=trader_id,
        status="Pending"
    ).count()

    accepted_requests = TransportRequest.query.filter_by(
        trader_id=trader_id,
        status="Accepted"
    ).count()

    completed_requests = TransportRequest.query.filter_by(
        trader_id=trader_id,
        status="Completed"
    ).count()

    bookings = Booking.query.filter_by(
        trader_id=trader_id
    ).order_by(
        Booking.created_at.desc()
    ).limit(5).all()

    return render_template(
        "trader/dashboard.html",
        requests=requests,
        bookings=bookings,
        total_requests=total_requests,
        pending_requests=pending_requests,
        accepted_requests=accepted_requests,
        completed_requests=completed_requests
    )