from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from app import db
from app.models import (
    TransportRequest,
    TruckMatch,
    Notification
)

from app.services.matching import find_matching_trucks


requests_bp = Blueprint(
    "requests",
    __name__,
    url_prefix="/requests"
)


def trader_required():
    return (
        session.get("logged_in") is True
        and session.get("user_role") == "trader"
    )


@requests_bp.route("/create", methods=["GET", "POST"])
def create_request():

    if not trader_required():
        flash(
            "Please login as a trader to create a transport request.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        goods_type = request.form.get(
            "goods_type",
            ""
        ).strip()

        quantity = request.form.get(
            "quantity",
            ""
        ).strip()

        quantity_unit = request.form.get(
            "quantity_unit",
            "tons"
        ).strip()

        pickup_location = request.form.get(
            "pickup_location",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        required_date = request.form.get(
            "required_date",
            ""
        ).strip()

        truck_type_required = request.form.get(
            "truck_type_required",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # Validate required fields
        if not all([
            goods_type,
            quantity,
            pickup_location,
            destination,
            required_date
        ]):

            flash(
                "Please complete all required fields.",
                "danger"
            )

            return render_template(
                "requests/create.html"
            )

        # Validate quantity
        try:

            quantity_value = float(quantity)

            if quantity_value <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid quantity greater than zero.",
                "danger"
            )

            return render_template(
                "requests/create.html"
            )

        # Validate date
        try:

            date_value = datetime.strptime(
                required_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Please enter a valid required date.",
                "danger"
            )

            return render_template(
                "requests/create.html"
            )

        # Create request
        transport_request = TransportRequest(

            trader_id=session["user_id"],

            goods_type=goods_type,

            quantity=quantity_value,

            quantity_unit=quantity_unit,

            pickup_location=pickup_location,

            destination=destination,

            required_date=date_value,

            truck_type_required=(
                truck_type_required
                if truck_type_required
                else None
            ),

            description=(
                description
                if description
                else None
            ),

            status="Pending"
        )

        db.session.add(
            transport_request
        )

        db.session.commit()

        # Find suitable trucks
        matches = find_matching_trucks(
            transport_request
        )

        # Save matches
        for match in matches:

            saved_match = TruckMatch(

                request_id=transport_request.id,

                truck_id=match["truck"].id,

                match_score=match["score"],

                capacity_score=match["capacity_score"],

                location_score=match["location_score"],

                availability_score=match["availability_score"],

                truck_type_score=match["truck_type_score"],

                destination_score=match["destination_score"],

                date_score=match["date_score"]
            )

            db.session.add(
                saved_match
            )

        # Update status if matches exist
        if matches:

            transport_request.status = "Matched"

        db.session.commit()

        flash(
            f"Request created successfully. "
            f"{len(matches)} suitable truck(s) found.",
            "success"
        )

        return redirect(
            url_for(
                "requests.request_details",
                request_id=transport_request.id
            )
        )

    return render_template(
        "requests/create.html"
    )


@requests_bp.route("/my-requests")
def my_requests():

    if not trader_required():

        flash(
            "Please login as a trader.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    requests_list = (
        TransportRequest.query
        .filter_by(
            trader_id=session["user_id"]
        )
        .order_by(
            TransportRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "requests/my_requests.html",
        requests=requests_list
    )


@requests_bp.route("/<int:request_id>")
def request_details(request_id):

    if not trader_required():

        flash(
            "Please login as a trader.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    transport_request = (
        TransportRequest.query
        .filter_by(
            id=request_id,
            trader_id=session["user_id"]
        )
        .first_or_404()
    )

    matches = (
        TruckMatch.query
        .filter_by(
            request_id=transport_request.id
        )
        .order_by(
            TruckMatch.match_score.desc()
        )
        .all()
    )

    return render_template(
        "requests/details.html",
        transport_request=transport_request,
        matches=matches
    )


@requests_bp.route(
    "/cancel/<int:request_id>",
    methods=["POST"]
)
def cancel_request(request_id):

    if not trader_required():

        flash(
            "Please login as a trader.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    transport_request = (
        TransportRequest.query
        .filter_by(
            id=request_id,
            trader_id=session["user_id"]
        )
        .first_or_404()
    )

    # Only these requests can be cancelled
    if transport_request.status not in [
        "Pending",
        "Matched",
        "Sent"
    ]:

        flash(
            "This transport request can no longer be cancelled.",
            "warning"
        )

        return redirect(
            url_for(
                "requests.request_details",
                request_id=request_id
            )
        )

    transport_request.status = "Cancelled"

    # Notify owners who received booking requests
    for booking in transport_request.bookings:

        if booking.status in [
            "Pending",
            "Accepted"
        ]:

            booking.status = "Cancelled"

            if booking.truck.availability == "Booked":

                booking.truck.availability = "Available"

            notification = Notification(

                user_id=booking.owner_id,

                title="Transport Request Cancelled",

                message=(
                    f"The trader has cancelled the transport request "
                    f"for {transport_request.goods_type} from "
                    f"{transport_request.pickup_location} to "
                    f"{transport_request.destination}."
                ),

                notification_type="request"
            )

            db.session.add(
                notification
            )

    db.session.commit()

    flash(
        "Transport request cancelled successfully.",
        "success"
    )

    return redirect(
        url_for(
            "requests.my_requests"
        )
    )