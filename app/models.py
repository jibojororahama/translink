from datetime import datetime

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    transport_requests = db.relationship(
        "TransportRequest",
        back_populates="trader",
        foreign_keys="TransportRequest.trader_id",
        cascade="all, delete-orphan"
    )

    trucks = db.relationship(
        "Truck",
        back_populates="owner",
        foreign_keys="Truck.owner_id",
        cascade="all, delete-orphan"
    )

    trader_bookings = db.relationship(
        "Booking",
        back_populates="trader",
        foreign_keys="Booking.trader_id"
    )

    owner_bookings = db.relationship(
        "Booking",
        back_populates="owner",
        foreign_keys="Booking.owner_id"
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Truck(db.Model):
    __tablename__ = "trucks"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    truck_name = db.Column(
        db.String(120),
        nullable=False
    )

    truck_type = db.Column(
        db.String(80),
        nullable=False
    )

    capacity = db.Column(
        db.Float,
        nullable=False
    )

    current_location = db.Column(
        db.String(200),
        nullable=False
    )

    destination_area = db.Column(
        db.String(200),
        nullable=True
    )

    availability = db.Column(
        db.String(30),
        default="Available",
        nullable=False
    )

    registration_number = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    owner = db.relationship(
        "User",
        back_populates="trucks",
        foreign_keys=[owner_id]
    )

    matches = db.relationship(
        "TruckMatch",
        back_populates="truck",
        cascade="all, delete-orphan"
    )

    bookings = db.relationship(
        "Booking",
        back_populates="truck"
    )


class TransportRequest(db.Model):
    __tablename__ = "transport_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    trader_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    goods_type = db.Column(
        db.String(120),
        nullable=False
    )

    quantity = db.Column(
        db.Float,
        nullable=False
    )

    quantity_unit = db.Column(
        db.String(30),
        default="tons",
        nullable=False
    )

    pickup_location = db.Column(
        db.String(200),
        nullable=False
    )

    destination = db.Column(
        db.String(200),
        nullable=False
    )

    required_date = db.Column(
        db.Date,
        nullable=False
    )

    truck_type_required = db.Column(
        db.String(80),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="Pending",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    trader = db.relationship(
        "User",
        back_populates="transport_requests",
        foreign_keys=[trader_id]
    )

    matches = db.relationship(
        "TruckMatch",
        back_populates="transport_request",
        cascade="all, delete-orphan"
    )

    bookings = db.relationship(
        "Booking",
        back_populates="transport_request"
    )


class TruckMatch(db.Model):
    __tablename__ = "truck_matches"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("transport_requests.id"),
        nullable=False
    )

    truck_id = db.Column(
        db.Integer,
        db.ForeignKey("trucks.id"),
        nullable=False
    )

    match_score = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    capacity_score = db.Column(
        db.Float,
        default=0
    )

    location_score = db.Column(
        db.Float,
        default=0
    )

    availability_score = db.Column(
        db.Float,
        default=0
    )

    truck_type_score = db.Column(
        db.Float,
        default=0
    )

    destination_score = db.Column(
        db.Float,
        default=0
    )

    date_score = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    transport_request = db.relationship(
        "TransportRequest",
        back_populates="matches"
    )

    truck = db.relationship(
        "Truck",
        back_populates="matches"
    )


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("transport_requests.id"),
        nullable=False
    )

    trader_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    truck_id = db.Column(
        db.Integer,
        db.ForeignKey("trucks.id"),
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    transport_request = db.relationship(
        "TransportRequest",
        back_populates="bookings"
    )

    trader = db.relationship(
        "User",
        back_populates="trader_bookings",
        foreign_keys=[trader_id]
    )

    owner = db.relationship(
        "User",
        back_populates="owner_bookings",
        foreign_keys=[owner_id]
    )

    truck = db.relationship(
        "Truck",
        back_populates="bookings"
    )

    payment = db.relationship(
        "Payment",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        nullable=False,
        unique=True
    )

    trader_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        default="NGN",
        nullable=False
    )

    reference = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending",
        nullable=False
    )

    payment_method = db.Column(
        db.String(50),
        default="Paystack",
        nullable=False
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    booking = db.relationship(
        "Booking",
        back_populates="payment"
    )

    trader = db.relationship(
        "User",
        foreign_keys=[trader_id]
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        default="general"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="notifications"
    )


class AdminActivity(db.Model):
    __tablename__ = "admin_activity"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    action = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class RegistrationVerification(db.Model):
    __tablename__ = "registration_verifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    code_hash = db.Column(
        db.String(255),
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )