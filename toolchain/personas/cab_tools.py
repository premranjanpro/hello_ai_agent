"""
cab_tools.py - Dedicated In-Memory Tools for Cab Booking Persona.
"""

import logging
import random
import time
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.cab")


class CabBookingToolsMixin:
    """Cab booking and ride management tools."""

    @llm.ai_callable(description="Calculate distance and estimated fare for a cab ride based on pickup, destination, and cab type.")
    async def estimate_cab_fare(
        self,
        pickup_location: Annotated[str, "The pickup point or starting location (e.g. 'Noida Sector 62')"],
        drop_location: Annotated[str, "The drop-off point or destination (e.g. 'Delhi Airport T3')"],
        cab_type: Annotated[str, "Type of cab requested: 'mini', 'sedan', or 'suv'"] = "sedan",
    ) -> str:
        logger.info(f"🚕 [Tool] estimate_cab_fare: {pickup_location} -> {drop_location} ({cab_type})")

        p_lower = pickup_location.lower()
        d_lower = drop_location.lower()

        base_km = 14.0
        if "airport" in p_lower or "airport" in d_lower:
            base_km = random.uniform(34.0, 42.0)
        elif "station" in p_lower or "station" in d_lower:
            base_km = random.uniform(18.0, 26.0)
        elif "noida" in p_lower and "gurgaon" in d_lower:
            base_km = random.uniform(45.0, 52.0)
        else:
            base_km = random.uniform(8.0, 22.0)

        distance_km = round(base_km, 1)

        rates = {
            "mini": {"base": 50, "rate": 12, "min_km": 3},
            "sedan": {"base": 70, "rate": 15, "min_km": 3},
            "suv": {"base": 100, "rate": 19, "min_km": 3},
        }
        cfg = rates.get(cab_type.lower(), rates["sedan"])
        extra_km = max(0.0, distance_km - cfg["min_km"])
        fare = int(round(cfg["base"] + (extra_km * cfg["rate"])))

        self.session_data["fare_estimate"] = {
            "pickup": pickup_location,
            "drop": drop_location,
            "cabType": cab_type.capitalize(),
            "distanceKm": distance_km,
            "estimatedFare": fare,
            "timestamp": time.time()
        }
        self.record_tool_invocation("estimate_cab_fare", {"pickup": pickup_location, "drop": drop_location, "fare": fare})

        return (
            f"Lagbhag {distance_km} kilometer hai. {cab_type.capitalize()} ka estimated fare Rs. {fare} hoga (GST inclusive). "
            "Kya main abhi cab confirm kar doon?"
        )

    @llm.ai_callable(description="Confirm and book a cab ride. Generates driver, vehicle number, and OTP in session memory.")
    async def book_cab_ride(
        self,
        pickup_location: Annotated[str, "Confirmed pickup location"],
        drop_location: Annotated[str, "Confirmed drop destination"],
        cab_type: Annotated[str, "Cab category: 'mini', 'sedan', or 'suv'"] = "sedan",
        passenger_name: Annotated[str, "Name of the passenger"] = "Customer",
    ) -> str:
        logger.info(f"🚕 [Tool] book_cab_ride: {passenger_name} ({cab_type}) {pickup_location} -> {drop_location}")

        prev_est = self.session_data.get("fare_estimate")
        if prev_est and prev_est.get("pickup") == pickup_location:
            fare = prev_est.get("estimatedFare", 350)
            distance_km = prev_est.get("distanceKm", 15.0)
        else:
            p_lower = pickup_location.lower()
            d_lower = drop_location.lower()
            distance_km = 38.0 if "airport" in p_lower or "airport" in d_lower else 14.5
            fare = 650 if "airport" in (p_lower + d_lower) else (350 if cab_type.lower() == "sedan" else 280)

        booking_id = f"CAB-{random.randint(1000, 9999)}"
        otp = str(random.randint(1000, 9999))
        drivers = ["Ramesh Kumar", "Suresh Yadav", "Vikram Singh", "Amit Sharma"]
        vehicles = [
            "White Swift Dzire (UP 16 DL 4920)",
            "Silver Hyundai Aura (DL 1Z 7831)",
            "Grey WagonR (HR 26 BY 2104)"
        ]
        driver = random.choice(drivers)
        vehicle = random.choice(vehicles)
        eta = random.randint(3, 6)

        self.session_data["cab_booking"] = {
            "bookingId": booking_id,
            "status": "CONFIRMED",
            "pickup": pickup_location,
            "drop": drop_location,
            "cabType": cab_type.capitalize(),
            "passengerName": passenger_name,
            "driverName": driver,
            "vehicleNumber": vehicle,
            "otp": otp,
            "etaMinutes": eta,
            "fare": fare,
            "distanceKm": distance_km,
            "bookedAt": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.record_tool_invocation("book_cab_ride", {"bookingId": booking_id, "otp": otp, "driver": driver})

        return (
            f"Aapki {cab_type} cab confirm ho gayi hai! Booking ID {booking_id} hai. "
            f"Driver {driver} agle {eta} minute me {vehicle} ke sath pahunch rahe hain. "
            f"Aapka OTP {otp} hai. Fare Rs. {fare} rahega."
        )

    @llm.ai_callable(description="Check real-time driver arrival ETA, live distance, and tracking status for an active booking.")
    async def track_driver_eta(
        self,
        booking_id: Annotated[str, "The booking ID (e.g. CAB-1234) or 'current' for active ride"] = "current",
    ) -> str:
        logger.info(f"📍 [Tool] track_driver_eta for booking={booking_id}")
        b = self.session_data.get("cab_booking")
        if b:
            remaining_mins = max(1, b.get("etaMinutes", 4) - 1)
            b["etaMinutes"] = remaining_mins
            return f"Driver {b['driverName']} ({b['vehicleNumber']}) bas {remaining_mins} minute me aapke pickup point par pahunchne wale hain. OTP {b['otp']} ready rakhiye!"
        return "Aapka driver on the way hai aur agle 3 se 4 minute me pickup location par pahunch jayega."
