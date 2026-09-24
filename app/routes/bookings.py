from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from app import db
from app.models import (
    Booking,
    Truck,
    TransportRequest,
    TruckMatch,
    Notification
)


bookings_bp = Blueprint(
    "bookings",
    __name__,
    url_prefix="/bookings"
)


def logged_in():
    return session.get("logged_in") is True


def trader_required():
    return (
        logged_in()
        and session.get("user_role") == "trader"
    )


def owner_required():
    return (
        logged_in()
        and session.get("user_role") == "owner"
    )


# ============================================================
# TRADER: CREATE BOOKING
# ============================================================

@bookings_bp.route(
    "/request/<int:request_id>/<int:truck_id>",
    methods=["POST"]
)
def create_booking(request_id, truck_id):

    if not trader_required():
        flash(
            "Please login as a trader to request a truck.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    transport_request = (
        TransportRequest.query
        .filter_by(
            id=request_id,
            trader_id=session["user_id"]
        )
        .first_or_404()
    )

    truck = Truck.query.filter_by(
        id=truck_id
    ).first_or_404()

    if truck.availability != "Available":
        flash(
            "This truck is no longer available.",
            "danger"
        )
        return redirect(
            url_for(
                "requests.request_details",
                request_id=request_id
            )
        )

    match = TruckMatch.query.filter_by(
        request_id=request_id,
        truck_id=truck_id
    ).first()

    if not match:
        flash(
            "This truck is not a valid match for this request.",
            "danger"
        )
        return redirect(
            url_for(
                "requests.request_details",
                request_id=request_id
            )
        )

    existing_booking = (
        Booking.query
        .filter_by(
            request_id=request_id,
            truck_id=truck_id
        )
        .filter(
            Booking.status.in_([
                "Pending",
                "Accepted"
            ])
        )
        .first()
    )

    if existing_booking:
        flash(
            "You have already requested this truck.",
            "warning"
        )
        return redirect(
            url_for("bookings.my_bookings")
        )

    booking = Booking(
        request_id=request_id,
        trader_id=session["user_id"],
        truck_id=truck_id,
        owner_id=truck.owner_id,
        status="Pending"
    )

    db.session.add(booking)

    transport_request.status = "Sent"

    notification = Notification(
        user_id=truck.owner_id,
        title="New Transport Request",
        message=(
            f"You have received a new transportation request "
            f"for {transport_request.goods_type} from "
            f"{transport_request.pickup_location} to "
            f"{transport_request.destination}."
        ),
        notification_type="booking"
    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Booking request sent successfully to the truck owner.",
        "success"
    )

    return redirect(
        url_for("bookings.my_bookings")
    )


# ============================================================
# TRADER: MY BOOKINGS
# ============================================================

@bookings_bp.route("/my-bookings")
def my_bookings():

    if not trader_required():
        flash(
            "Please login as a trader.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    bookings = (
        Booking.query
        .filter_by(
            trader_id=session["user_id"]
        )
        .order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    return render_template(
        "bookings/my_bookings.html",
        bookings=bookings
    )


# ============================================================
# OWNER: BOOKING REQUESTS
# ============================================================

@bookings_bp.route("/owner-requests")
def owner_requests():

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    owner_id = session["user_id"]

    bookings = (
        Booking.query
        .join(
            Truck,
            Booking.truck_id == Truck.id
        )
        .filter(
            Truck.owner_id == owner_id
        )
        .order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    return render_template(
        "bookings/owner_requests.html",
        bookings=bookings
    )


# ============================================================
# OWNER: ACCEPT BOOKING
# ============================================================

@bookings_bp.route(
    "/accept/<int:booking_id>",
    methods=["POST"]
)
def accept_booking(booking_id):

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    booking = (
        Booking.query
        .join(
            Truck,
            Booking.truck_id == Truck.id
        )
        .filter(
            Booking.id == booking_id,
            Truck.owner_id == session["user_id"]
        )
        .first_or_404()
    )

    if booking.status != "Pending":
        flash(
            "This booking is no longer pending.",
            "warning"
        )
        return redirect(
            url_for("bookings.owner_requests")
        )

    if booking.truck.availability != "Available":
        flash(
            "This truck is no longer available.",
            "danger"
        )
        return redirect(
            url_for("bookings.owner_requests")
        )

    booking.status = "Accepted"

    booking.truck.availability = "Booked"

    booking.transport_request.status = "Accepted"

    # Reject other pending requests for this same truck
    other_bookings = (
        Booking.query
        .filter(
            Booking.truck_id == booking.truck_id,
            Booking.id != booking.id,
            Booking.status == "Pending"
        )
        .all()
    )

    for other in other_bookings:

        other.status = "Rejected"

        other_notification = Notification(
            user_id=other.trader_id,
            title="Booking Request Rejected",
            message=(
                f"The truck {booking.truck.truck_name} "
                f"has been booked by another trader."
            ),
            notification_type="booking"
        )

        db.session.add(other_notification)

    notification = Notification(
        user_id=booking.trader_id,
        title="Booking Accepted",
        message=(
            f"Your request for "
            f"{booking.truck.truck_name} "
            f"has been accepted by the truck owner."
        ),
        notification_type="booking"
    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Booking accepted successfully.",
        "success"
    )

    return redirect(
        url_for("bookings.owner_requests")
    )


# ============================================================
# OWNER: REJECT BOOKING
# ============================================================

@bookings_bp.route(
    "/reject/<int:booking_id>",
    methods=["POST"]
)
def reject_booking(booking_id):

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    booking = (
        Booking.query
        .join(
            Truck,
            Booking.truck_id == Truck.id
        )
        .filter(
            Booking.id == booking_id,
            Truck.owner_id == session["user_id"]
        )
        .first_or_404()
    )

    if booking.status != "Pending":
        flash(
            "This booking is no longer pending.",
            "warning"
        )
        return redirect(
            url_for("bookings.owner_requests")
        )

    booking.status = "Rejected"

    booking.transport_request.status = "Rejected"

    notification = Notification(
        user_id=booking.trader_id,
        title="Booking Rejected",
        message=(
            f"Your request for "
            f"{booking.truck.truck_name} "
            f"was rejected by the truck owner."
        ),
        notification_type="booking"
    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Booking rejected.",
        "success"
    )

    return redirect(
        url_for("bookings.owner_requests")
    )


# ============================================================
# TRADER: CANCEL BOOKING
# ============================================================

@bookings_bp.route(
    "/cancel/<int:booking_id>",
    methods=["POST"]
)
def cancel_booking(booking_id):

    if not trader_required():
        flash(
            "Please login as a trader.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    booking = (
        Booking.query
        .filter_by(
            id=booking_id,
            trader_id=session["user_id"]
        )
        .first_or_404()
    )

    if booking.status not in [
        "Pending",
        "Accepted"
    ]:
        flash(
            "This booking cannot be cancelled.",
            "warning"
        )
        return redirect(
            url_for("bookings.my_bookings")
        )

    booking.status = "Cancelled"

    if booking.truck.availability == "Booked":
        booking.truck.availability = "Available"

    booking.transport_request.status = "Cancelled"

    notification = Notification(
        user_id=booking.owner_id,
        title="Booking Cancelled",
        message=(
            f"The trader has cancelled the booking "
            f"for {booking.truck.truck_name}."
        ),
        notification_type="booking"
    )

    db.session.add(notification)

    db.session.commit()

    flash(
        "Booking cancelled successfully.",
        "success"
    )

    return redirect(
        url_for("bookings.my_bookings")
    )