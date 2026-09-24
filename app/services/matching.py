from datetime import date

from app.models import Truck


TRUCK_TYPE_ALIASES = {
    "box truck": "Box Truck",
    "cargo truck": "Cargo Truck",
    "refrigerated truck": "Refrigerated Truck",
    "flatbed": "Flatbed",
    "tipper": "Tipper",
    "tanker": "Tanker",
    "trailer": "Trailer",
    "other": "Other",
}


def normalize_text(value):
    if not value:
        return ""

    return " ".join(value.lower().strip().split())


def location_match(pickup_location, truck_location):
    """
    Basic Nigeria-focused location matching.

    Exact city/state match receives full points.
    Same state or partial location match receives partial points.
    """
    pickup = normalize_text(pickup_location)
    truck = normalize_text(truck_location)

    if not pickup or not truck:
        return 0

    if pickup == truck:
        return 20

    pickup_parts = set(pickup.replace(",", " ").split())
    truck_parts = set(truck.replace(",", " ").split())

    common = pickup_parts.intersection(truck_parts)

    if common:
        return 15

    return 5


def calculate_match(request_obj, truck):
    """
    Calculate how suitable a truck is for a transportation request.

    Maximum score: 100
    """

    score = 0

    # --------------------------------
    # 1. CAPACITY - 30 POINTS
    # --------------------------------

    capacity_score = 0

    if truck.capacity >= request_obj.quantity:

        if truck.capacity == request_obj.quantity:
            capacity_score = 30

        elif truck.capacity <= request_obj.quantity * 1.5:
            capacity_score = 28

        elif truck.capacity <= request_obj.quantity * 2:
            capacity_score = 25

        else:
            capacity_score = 20

    else:
        capacity_score = 0

    # --------------------------------
    # 2. LOCATION - 20 POINTS
    # --------------------------------

    location_score = location_match(
        request_obj.pickup_location,
        truck.current_location
    )

    # --------------------------------
    # 3. AVAILABILITY - 15 POINTS
    # --------------------------------

    availability_score = 0

    if normalize_text(truck.availability) == "available":
        availability_score = 15

    # --------------------------------
    # 4. TRUCK TYPE - 15 POINTS
    # --------------------------------

    truck_type_score = 0

    requested_type = normalize_text(
        request_obj.truck_type_required
    )

    actual_type = normalize_text(
        truck.truck_type
    )

    if not requested_type:
        truck_type_score = 15

    elif requested_type == actual_type:
        truck_type_score = 15

    elif TRUCK_TYPE_ALIASES.get(requested_type) == truck.truck_type:
        truck_type_score = 15

    else:
        truck_type_score = 5

    # --------------------------------
    # 5. DESTINATION - 10 POINTS
    # --------------------------------

    destination_score = 0

    requested_destination = normalize_text(
        request_obj.destination
    )

    truck_destination = normalize_text(
        truck.destination_area
    )

    if not truck_destination:
        destination_score = 5

    elif requested_destination == truck_destination:
        destination_score = 10

    else:
        requested_words = set(
            requested_destination.replace(",", " ").split()
        )

        destination_words = set(
            truck_destination.replace(",", " ").split()
        )

        if requested_words.intersection(destination_words):
            destination_score = 7

        else:
            destination_score = 3

    # --------------------------------
    # 6. DATE - 10 POINTS
    # --------------------------------

    date_score = 0

    if request_obj.required_date:

        today = date.today()

        if request_obj.required_date >= today:
            date_score = 10

        else:
            date_score = 0

    # --------------------------------
    # TOTAL
    # --------------------------------

    score = (
        capacity_score
        + location_score
        + availability_score
        + truck_type_score
        + destination_score
        + date_score
    )

    return {
        "score": round(score, 1),
        "capacity_score": capacity_score,
        "location_score": location_score,
        "availability_score": availability_score,
        "truck_type_score": truck_type_score,
        "destination_score": destination_score,
        "date_score": date_score,
    }


def find_matching_trucks(request_obj):
    """
    Find suitable available trucks and rank them
    from highest to lowest match score.
    """

    trucks = Truck.query.filter_by(
        availability="Available"
    ).all()

    matches = []

    for truck in trucks:

        result = calculate_match(
            request_obj,
            truck
        )

        # Never recommend a truck that cannot carry the load.
        if truck.capacity < request_obj.quantity:
            continue

        # Ignore very poor matches.
        if result["score"] < 40:
            continue

        matches.append({
            "truck": truck,
            **result
        })

    matches.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return matches