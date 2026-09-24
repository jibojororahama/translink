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
    User,
    Truck,
    TransportRequest,
    Booking,
    AdminActivity
)


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def admin_required():
    return (
        session.get("logged_in") is True
        and session.get("user_role") == "admin"
    )


def record_activity(action, description):
    activity = AdminActivity(
        admin_id=session.get("user_id"),
        action=action,
        description=description
    )

    db.session.add(activity)


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.route("/")
def dashboard():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    total_users = User.query.count()
    total_traders = User.query.filter_by(role="trader").count()
    total_owners = User.query.filter_by(role="owner").count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()

    total_trucks = Truck.query.count()
    available_trucks = Truck.query.filter_by(
        availability="Available"
    ).count()
    booked_trucks = Truck.query.filter_by(
        availability="Booked"
    ).count()
    unavailable_trucks = Truck.query.filter_by(
        availability="Unavailable"
    ).count()

    total_requests = TransportRequest.query.count()
    pending_requests = TransportRequest.query.filter_by(
        status="Pending"
    ).count()
    matched_requests = TransportRequest.query.filter_by(
        status="Matched"
    ).count()
    accepted_requests = TransportRequest.query.filter_by(
        status="Accepted"
    ).count()
    completed_requests = TransportRequest.query.filter_by(
        status="Completed"
    ).count()

    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(
        status="Pending"
    ).count()
    accepted_bookings = Booking.query.filter_by(
        status="Accepted"
    ).count()
    rejected_bookings = Booking.query.filter_by(
        status="Rejected"
    ).count()
    completed_bookings = Booking.query.filter_by(
        status="Completed"
    ).count()

    recent_users = (
        User.query
        .order_by(User.created_at.desc())
        .limit(8)
        .all()
    )

    recent_trucks = (
        Truck.query
        .order_by(Truck.created_at.desc())
        .limit(8)
        .all()
    )

    recent_requests = (
        TransportRequest.query
        .order_by(TransportRequest.created_at.desc())
        .limit(8)
        .all()
    )

    recent_bookings = (
        Booking.query
        .order_by(Booking.created_at.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",

        total_users=total_users,
        total_traders=total_traders,
        total_owners=total_owners,
        active_users=active_users,
        inactive_users=inactive_users,

        total_trucks=total_trucks,
        available_trucks=available_trucks,
        booked_trucks=booked_trucks,
        unavailable_trucks=unavailable_trucks,

        total_requests=total_requests,
        pending_requests=pending_requests,
        matched_requests=matched_requests,
        accepted_requests=accepted_requests,
        completed_requests=completed_requests,

        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
        rejected_bookings=rejected_bookings,
        completed_bookings=completed_bookings,

        recent_users=recent_users,
        recent_trucks=recent_trucks,
        recent_requests=recent_requests,
        recent_bookings=recent_bookings
    )


# =========================================================
# USER MANAGEMENT
# =========================================================

@admin_bp.route("/users")
def users():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%")
            )
        )

    users_list = (
        query
        .order_by(User.created_at.desc())
        .all()
    )

    return render_template(
        "admin/users.html",
        users=users_list,
        search=search
    )


@admin_bp.route(
    "/users/toggle/<int:user_id>",
    methods=["POST"]
)
def toggle_user(user_id):

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)

    if user.id == session.get("user_id"):
        flash(
            "You cannot deactivate your own administrator account.",
            "danger"
        )
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active

    status = "activated" if user.is_active else "deactivated"

    record_activity(
        "User Status Changed",
        f"Administrator {status} user account: {user.full_name}"
    )

    db.session.commit()

    flash(
        f"{user.full_name}'s account has been {status}.",
        "success"
    )

    return redirect(url_for("admin.users"))


# =========================================================
# TRUCK MANAGEMENT
# =========================================================

@admin_bp.route("/trucks")
def trucks():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    availability = request.args.get("availability", "").strip()
    truck_type = request.args.get("truck_type", "").strip()

    query = Truck.query

    if search:
        query = query.join(User).filter(
            db.or_(
                Truck.truck_name.ilike(f"%{search}%"),
                Truck.registration_number.ilike(f"%{search}%"),
                Truck.current_location.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )

    if availability:
        query = query.filter(
            Truck.availability == availability
        )

    if truck_type:
        query = query.filter(
            Truck.truck_type == truck_type
        )

    trucks_list = (
        query
        .order_by(Truck.created_at.desc())
        .all()
    )

    return render_template(
        "admin/trucks.html",
        trucks=trucks_list,
        search=search,
        availability=availability,
        truck_type=truck_type
    )


@admin_bp.route(
    "/trucks/toggle/<int:truck_id>",
    methods=["POST"]
)
def toggle_truck(truck_id):

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    truck = Truck.query.get_or_404(truck_id)

    if truck.availability == "Unavailable":
        truck.availability = "Available"
        message = f"{truck.truck_name} has been activated."
    else:
        truck.availability = "Unavailable"
        message = f"{truck.truck_name} has been marked as unavailable."

    record_activity(
        "Truck Availability Changed",
        message
    )

    db.session.commit()

    flash(message, "success")

    return redirect(url_for("admin.trucks"))


# =========================================================
# TRANSPORT REQUEST MANAGEMENT
# =========================================================

@admin_bp.route("/requests")
def transport_requests():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    status = request.args.get("status", "").strip()

    query = TransportRequest.query

    if status:
        query = query.filter_by(status=status)

    requests_list = (
        query
        .order_by(
            TransportRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/requests.html",
        requests=requests_list,
        status=status
    )


# =========================================================
# BOOKING MANAGEMENT
# =========================================================

@admin_bp.route("/bookings")
def bookings():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    status = request.args.get("status", "").strip()

    query = Booking.query

    if status:
        query = query.filter_by(status=status)

    bookings_list = (
        query
        .order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/bookings.html",
        bookings=bookings_list,
        status=status
    )


# =========================================================
# ACTIVITY LOG
# =========================================================

@admin_bp.route("/activity")
def activity():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    activities = (
        AdminActivity.query
        .order_by(
            AdminActivity.created_at.desc()
        )
        .limit(100)
        .all()
    )

    return render_template(
        "admin/activity.html",
        activities=activities
    )


# =========================================================
# REPORTS & ANALYTICS
# =========================================================

@admin_bp.route("/reports")
def reports():

    if not admin_required():
        flash("Administrator access is required.", "danger")
        return redirect(url_for("auth.login"))

    # USER STATISTICS

    total_users = User.query.count()

    traders = User.query.filter_by(
        role="trader"
    ).count()

    owners = User.query.filter_by(
        role="owner"
    ).count()

    admins = User.query.filter_by(
        role="admin"
    ).count()

    active_users = User.query.filter_by(
        is_active=True
    ).count()

    inactive_users = User.query.filter_by(
        is_active=False
    ).count()


    # TRUCK STATISTICS

    total_trucks = Truck.query.count()

    available_trucks = Truck.query.filter_by(
        availability="Available"
    ).count()

    booked_trucks = Truck.query.filter_by(
        availability="Booked"
    ).count()

    unavailable_trucks = Truck.query.filter_by(
        availability="Unavailable"
    ).count()

    maintenance_trucks = Truck.query.filter_by(
        availability="Maintenance"
    ).count()


    # REQUEST STATISTICS

    total_requests = TransportRequest.query.count()

    pending_requests = TransportRequest.query.filter_by(
        status="Pending"
    ).count()

    matched_requests = TransportRequest.query.filter_by(
        status="Matched"
    ).count()

    sent_requests = TransportRequest.query.filter_by(
        status="Sent"
    ).count()

    accepted_requests = TransportRequest.query.filter_by(
        status="Accepted"
    ).count()

    rejected_requests = TransportRequest.query.filter_by(
        status="Rejected"
    ).count()

    cancelled_requests = TransportRequest.query.filter_by(
        status="Cancelled"
    ).count()

    transit_requests = TransportRequest.query.filter_by(
        status="In Transit"
    ).count()

    completed_requests = TransportRequest.query.filter_by(
        status="Completed"
    ).count()


    # BOOKING STATISTICS

    total_bookings = Booking.query.count()

    pending_bookings = Booking.query.filter_by(
        status="Pending"
    ).count()

    accepted_bookings = Booking.query.filter_by(
        status="Accepted"
    ).count()

    rejected_bookings = Booking.query.filter_by(
        status="Rejected"
    ).count()

    cancelled_bookings = Booking.query.filter_by(
        status="Cancelled"
    ).count()

    transit_bookings = Booking.query.filter_by(
        status="In Transit"
    ).count()

    completed_bookings = Booking.query.filter_by(
        status="Completed"
    ).count()


    # RECENT ACTIVITY

    recent_activity = (
        AdminActivity.query
        .order_by(AdminActivity.created_at.desc())
        .limit(10)
        .all()
    )


    return render_template(
        "admin/reports.html",

        total_users=total_users,
        traders=traders,
        owners=owners,
        admins=admins,
        active_users=active_users,
        inactive_users=inactive_users,

        total_trucks=total_trucks,
        available_trucks=available_trucks,
        booked_trucks=booked_trucks,
        unavailable_trucks=unavailable_trucks,
        maintenance_trucks=maintenance_trucks,

        total_requests=total_requests,
        pending_requests=pending_requests,
        matched_requests=matched_requests,
        sent_requests=sent_requests,
        accepted_requests=accepted_requests,
        rejected_requests=rejected_requests,
        cancelled_requests=cancelled_requests,
        transit_requests=transit_requests,
        completed_requests=completed_requests,

        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
        rejected_bookings=rejected_bookings,
        cancelled_bookings=cancelled_bookings,
        transit_bookings=transit_bookings,
        completed_bookings=completed_bookings,

        recent_activity=recent_activity
    )