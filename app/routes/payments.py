from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from app import db
from app.models import Booking, Payment, User
import requests
import uuid
from datetime import datetime

payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/payments"
)


@payments_bp.route("/<int:booking_id>")
def payment_page(booking_id):

    if "user_id" not in session:
        flash("Please login to continue.", "warning")
        return redirect(url_for("auth.login"))

    booking = Booking.query.filter_by(
        id=booking_id,
        trader_id=session["user_id"]
    ).first_or_404()

    if booking.status != "Accepted":
        flash(
            "Payment is only available for accepted bookings.",
            "warning"
        )
        return redirect(url_for("bookings.my_bookings"))

    if booking.fare <= 0:
        flash(
            "This booking does not have a valid fare.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    payment = Payment.query.filter_by(
        booking_id=booking.id
    ).first()

    return render_template(
        "payments/pay.html",
        booking=booking,
        payment=payment
    )


@payments_bp.route(
    "/initialize/<int:booking_id>",
    methods=["POST"]
)
def initialize_payment(booking_id):

    if "user_id" not in session:
        flash("Please login to continue.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    booking = Booking.query.filter_by(
        id=booking_id,
        trader_id=user_id
    ).first_or_404()

    if booking.status != "Accepted":
        flash(
            "You can only pay for an accepted booking.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    if booking.fare <= 0:
        flash(
            "This booking does not have a valid fare.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    user = User.query.get_or_404(user_id)

    secret_key = current_app.config.get(
        "PAYSTACK_SECRET_KEY"
    )

    if not secret_key:
        flash(
            "Payment service is not configured.",
            "danger"
        )
        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    payment = Payment.query.filter_by(
        booking_id=booking.id
    ).first()

    if payment and payment.status == "Paid":
        flash(
            "This booking has already been paid for.",
            "info"
        )
        return redirect(
            url_for("payments.payment_history")
        )

    # Always create a fresh Paystack reference
    # for a new payment attempt.
    new_reference = (
        "TL-"
        + str(booking.id)
        + "-"
        + uuid.uuid4().hex.upper()
    )

    if not payment:

        payment = Payment(
            booking_id=booking.id,
            trader_id=user_id,
            amount=booking.fare,
            currency="NGN",
            reference=new_reference,
            status="Pending",
            payment_method="Paystack"
        )

        db.session.add(payment)

    else:

        payment.amount = booking.fare
        payment.currency = "NGN"
        payment.reference = new_reference
        payment.status = "Pending"
        payment.payment_method = "Paystack"
        payment.paid_at = None

    db.session.commit()

    payload = {
        "email": user.email,
        "amount": int(round(float(booking.fare) * 100)),
        "currency": "NGN",
        "reference": new_reference,
        "callback_url": url_for(
            "payments.payment_callback",
            _external=True
        ),
        "metadata": {
            "booking_id": booking.id,
            "trader_id": user_id
        }
    }

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30
        )

        data = response.json()

    except requests.RequestException:

        flash(
            "Unable to connect to the payment service. Please try again.",
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    if response.status_code != 200 or not data.get("status"):

        flash(
            data.get(
                "message",
                "Payment initialization failed."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    authorization_url = (
        data.get("data", {})
        .get("authorization_url")
    )

    if not authorization_url:

        flash(
            "Paystack did not return a payment link.",
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    return redirect(authorization_url)


@payments_bp.route("/callback")
def payment_callback():

    reference = request.args.get("reference")

    if not reference:
        flash(
            "Payment reference was not provided.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    secret_key = current_app.config.get(
        "PAYSTACK_SECRET_KEY"
    )

    if not secret_key:
        flash(
            "Payment service is not configured.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=30
        )

        data = response.json()

    except requests.RequestException:

        flash(
            "Unable to verify your payment. Please try again.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    if response.status_code != 200 or not data.get("status"):

        flash(
            "Payment verification failed.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    transaction = data.get("data", {})

    payment = Payment.query.filter_by(
        reference=reference
    ).first()

    if not payment:

        flash(
            "Payment record could not be found.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    booking = Booking.query.get(payment.booking_id)

    if not booking:

        flash(
            "Associated booking could not be found.",
            "danger"
        )
        return redirect(url_for("bookings.my_bookings"))

    expected_amount = int(
        round(float(booking.fare) * 100)
    )

    paid_amount = int(
        transaction.get("amount", 0)
    )

    if paid_amount != expected_amount:

        payment.status = "Failed"
        db.session.commit()

        flash(
            "The payment amount could not be verified.",
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    if transaction.get("currency") != "NGN":

        payment.status = "Failed"
        db.session.commit()

        flash(
            "The payment currency could not be verified.",
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    if transaction.get("status") != "success":

        payment.status = "Failed"
        db.session.commit()

        flash(
            "Payment was not successful.",
            "danger"
        )

        return redirect(
            url_for(
                "payments.payment_page",
                booking_id=booking.id
            )
        )

    payment.status = "Paid"
    payment.payment_method = "Paystack"
    payment.paid_at = datetime.utcnow()

    db.session.commit()

    return render_template(
        "payments/success.html",
        booking=booking,
        payment=payment
    )


@payments_bp.route("/history")
def payment_history():

    if "user_id" not in session:
        flash("Please login to continue.", "warning")
        return redirect(url_for("auth.login"))

    payments = (
        Payment.query
        .filter_by(
            trader_id=session["user_id"]
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    return render_template(
        "payments/history.html",
        payments=payments
    )
