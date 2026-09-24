from flask import Blueprint, render_template, redirect, url_for, session, flash

from app import db
from app.models import Truck, Booking


owner_bp = Blueprint(
    "owner",
    __name__,
    url_prefix="/owner"
)


def owner_required():
    return (
        session.get("logged_in") is True
        and session.get("user_role") == "owner"
    )


@owner_bp.route("/")
def dashboard():

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    owner_id = session["user_id"]

    # Owner's trucks
    trucks = (
        Truck.query
        .filter_by(owner_id=owner_id)
        .order_by(Truck.created_at.desc())
        .all()
    )

    total_trucks = len(trucks)

    available_trucks = sum(
        1 for truck in trucks
        if truck.availability == "Available"
    )

    unavailable_trucks = sum(
        1 for truck in trucks
        if truck.availability == "Unavailable"
    )

    booked_trucks = sum(
        1 for truck in trucks
        if truck.availability == "Booked"
    )

    # Booking requests belonging to this owner
    bookings = (
        Booking.query
        .join(Truck)
        .filter(
            Truck.owner_id == owner_id
        )
        .order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    total_bookings = len(bookings)

    pending_bookings = sum(
        1 for booking in bookings
        if booking.status == "Pending"
    )

    accepted_bookings = sum(
        1 for booking in bookings
        if booking.status == "Accepted"
    )

    rejected_bookings = sum(
        1 for booking in bookings
        if booking.status == "Rejected"
    )

    completed_bookings = sum(
        1 for booking in bookings
        if booking.status == "Completed"
    )

    recent_bookings = bookings[:5]

    return render_template(
        "owner/dashboard.html",
        trucks=trucks,
        bookings=bookings,
        recent_bookings=recent_bookings,
        total_trucks=total_trucks,
        available_trucks=available_trucks,
        unavailable_trucks=unavailable_trucks,
        booked_trucks=booked_trucks,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
        rejected_bookings=rejected_bookings,
        completed_bookings=completed_bookings
    )