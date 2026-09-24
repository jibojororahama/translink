import os


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "translink-development-secret-key-change-in-production"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///translink.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paystack
    PAYSTACK_SECRET_KEY = os.environ.get(
        "PAYSTACK_SECRET_KEY",
        ""
    )