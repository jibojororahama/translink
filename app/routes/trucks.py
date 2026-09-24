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
from app.models import Truck


trucks_bp = Blueprint(
    "trucks",
    __name__,
    url_prefix="/trucks"
)


def owner_required():
    return (
        session.get("logged_in") is True
        and session.get("user_role") == "owner"
    )


@trucks_bp.route("/my-trucks")
def my_trucks():

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(
            url_for("auth.login")
        )

    trucks = (
        Truck.query
        .filter_by(owner_id=session["user_id"])
        .order_by(Truck.created_at.desc())
        .all()
    )

    return render_template(
        "trucks/my_trucks.html",
        trucks=trucks
    )


@trucks_bp.route("/add", methods=["GET", "POST"])
def add_truck():

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        truck_name = request.form.get(
            "truck_name",
            ""
        ).strip()

        truck_type = request.form.get(
            "truck_type",
            ""
        ).strip()

        capacity = request.form.get(
            "capacity",
            ""
        ).strip()

        current_location = request.form.get(
            "current_location",
            ""
        ).strip()

        destination_area = request.form.get(
            "destination_area",
            ""
        ).strip()

        availability = request.form.get(
            "availability",
            "Available"
        ).strip()

        registration_number = request.form.get(
            "registration_number",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not all([
            truck_name,
            truck_type,
            capacity,
            current_location
        ]):

            flash(
                "Please complete all required truck fields.",
                "danger"
            )

            return render_template(
                "trucks/add.html"
            )

        try:

            capacity_value = float(capacity)

            if capacity_value <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid truck capacity.",
                "danger"
            )

            return render_template(
                "trucks/add.html"
            )

        valid_availability = [
            "Available",
            "Booked",
            "Unavailable",
            "Maintenance"
        ]

        if availability not in valid_availability:
            availability = "Available"

        truck = Truck(

            owner_id=session["user_id"],

            truck_name=truck_name,

            truck_type=truck_type,

            capacity=capacity_value,

            current_location=current_location,

            destination_area=(
                destination_area
                if destination_area
                else None
            ),

            availability=availability,

            registration_number=(
                registration_number
                if registration_number
                else None
            ),

            description=(
                description
                if description
                else None
            )
        )

        db.session.add(truck)
        db.session.commit()

        flash(
            "Truck added successfully.",
            "success"
        )

        return redirect(
            url_for("trucks.my_trucks")
        )

    return render_template(
        "trucks/add.html"
    )


@trucks_bp.route(
    "/edit/<int:truck_id>",
    methods=["GET", "POST"]
)
def edit_truck(truck_id):

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(
            url_for("auth.login")
        )

    truck = (
        Truck.query
        .filter_by(
            id=truck_id,
            owner_id=session["user_id"]
        )
        .first_or_404()
    )

    if request.method == "POST":

        truck_name = request.form.get(
            "truck_name",
            ""
        ).strip()

        truck_type = request.form.get(
            "truck_type",
            ""
        ).strip()

        capacity = request.form.get(
            "capacity",
            ""
        ).strip()

        current_location = request.form.get(
            "current_location",
            ""
        ).strip()

        destination_area = request.form.get(
            "destination_area",
            ""
        ).strip()

        availability = request.form.get(
            "availability",
            "Available"
        ).strip()

        registration_number = request.form.get(
            "registration_number",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not all([
            truck_name,
            truck_type,
            capacity,
            current_location
        ]):

            flash(
                "Please complete all required truck fields.",
                "danger"
            )

            return render_template(
                "trucks/edit.html",
                truck=truck
            )

        try:

            capacity_value = float(capacity)

            if capacity_value <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid truck capacity.",
                "danger"
            )

            return render_template(
                "trucks/edit.html",
                truck=truck
            )

        valid_availability = [
            "Available",
            "Booked",
            "Unavailable",
            "Maintenance"
        ]

        if availability not in valid_availability:
            availability = "Available"

        truck.truck_name = truck_name
        truck.truck_type = truck_type
        truck.capacity = capacity_value
        truck.current_location = current_location
        truck.destination_area = (
            destination_area
            if destination_area
            else None
        )
        truck.availability = availability
        truck.registration_number = (
            registration_number
            if registration_number
            else None
        )
        truck.description = (
            description
            if description
            else None
        )

        db.session.commit()

        flash(
            "Truck updated successfully.",
            "success"
        )

        return redirect(
            url_for("trucks.my_trucks")
        )

    return render_template(
        "trucks/edit.html",
        truck=truck
    )


@trucks_bp.route(
    "/delete/<int:truck_id>",
    methods=["POST"]
)
def delete_truck(truck_id):

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(
            url_for("auth.login")
        )

    truck = (
        Truck.query
        .filter_by(
            id=truck_id,
            owner_id=session["user_id"]
        )
        .first_or_404()
    )

    if truck.availability == "Booked":

        flash(
            "A booked truck cannot be deleted.",
            "danger"
        )

        return redirect(
            url_for("trucks.my_trucks")
        )

    if truck.bookings:

        flash(
            "This truck has booking history and cannot be deleted. "
            "Set it to Unavailable instead.",
            "warning"
        )

        return redirect(
            url_for("trucks.my_trucks")
        )

    db.session.delete(truck)
    db.session.commit()

    flash(
        "Truck deleted successfully.",
        "success"
    )

    return redirect(
        url_for("trucks.my_trucks")
    )


@trucks_bp.route(
    "/toggle/<int:truck_id>",
    methods=["POST"]
)
def toggle_availability(truck_id):

    if not owner_required():
        flash(
            "Please login as a truck owner.",
            "warning"
        )
        return redirect(
            url_for("auth.login")
        )

    truck = (
        Truck.query
        .filter_by(
            id=truck_id,
            owner_id=session["user_id"]
        )
        .first_or_404()
    )

    if truck.availability == "Available":

        truck.availability = "Unavailable"

    elif truck.availability == "Unavailable":

        truck.availability = "Available"

    else:

        flash(
            "Only Available and Unavailable trucks can be toggled.",
            "warning"
        )

        return redirect(
            url_for("trucks.my_trucks")
        )

    db.session.commit()

    flash(
        f"Truck is now {truck.availability.lower()}.",
        "success"
    )

    return redirect(
        url_for("trucks.my_trucks")
    )