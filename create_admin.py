from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User


app = create_app()


def main():
    print("=" * 50)
    print("TRANSLINK ADMINISTRATOR SETUP")
    print("=" * 50)

    with app.app_context():

        full_name = input("Admin full name: ").strip()
        email = input("Admin email: ").strip().lower()
        phone = input("Admin phone: ").strip()

        if not full_name or not email or not phone:
            print("\nAll fields are required.")
            return

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print("\nAn account with this email already exists.")

            if existing_user.role == "admin":
                print("This account is already an administrator.")
            else:
                print(
                    f"This email belongs to a {existing_user.role} account."
                )

            return

        password = getpass("Admin password: ")
        confirm_password = getpass("Confirm password: ")

        if not password:
            print("\nPassword cannot be empty.")
            return

        if len(password) < 6:
            print("\nPassword must contain at least 6 characters.")
            return

        if password != confirm_password:
            print("\nPasswords do not match.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role="admin",
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("\n" + "=" * 50)
        print("ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 50)
        print(f"Name:  {full_name}")
        print(f"Email: {email}")
        print("Role:  Administrator")
        print("=" * 50)


if __name__ == "__main__":
    main()