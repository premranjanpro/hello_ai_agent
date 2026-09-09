"""
sales_tools.py - Dedicated In-Memory Tools for B2B Software Sales (Travel Packages & Cab Dispatch Solutions).
Enables software feature pitching, instant pricing/ROI calculation, live demo scheduling,
brochure dispatch via WhatsApp, and dynamic on-the-fly persona switching.
"""

import logging
import time
from typing import Annotated, Optional, Dict, Any, List
from livekit.agents import llm

logger = logging.getLogger("toolchain.personas.sales")


class SoftwareSalesToolsMixin:
    """B2B Software Sales tools for Travel Packages & Cab Booking Solutions."""

    def _ensure_sales_session(self):
        """Initializes sales session tracking."""
        if not self.session_data.get("software_lead"):
            self.session_data["software_lead"] = {
                "client_name": "",
                "business_name": "",
                "phone_number": "",
                "interested_solution": "",
                "fleet_size": 0,
                "quoted_price": None,
                "demo_scheduled": None,
                "brochure_sent": False,
            }

    @llm.ai_callable(description="Pitch comprehensive software features for Cab Booking/Fleet Dispatch or Travel Package Agency CRM.")
    async def pitch_software_features(
        self,
        solution_type: Annotated[str, "Type of software: 'cab_dispatch' (Cab booking app & driver fleet), 'travel_package_crm' (Tour package & itinerary booking portal), or 'complete_suite' (both)"],
    ) -> str:
        self._ensure_sales_session()
        st = solution_type.lower()
        self.session_data["software_lead"]["interested_solution"] = solution_type
        logger.info(f"💼 [SalesTool] pitch_software_features: {solution_type}")
        self.record_tool_invocation("pitch_software_features", {"solution": solution_type})

        if "cab" in st:
            return (
                "Hamara Cab Dispatch Software poora ready-to-use solution hai! Isme aapko milta hai: "
                "1. White-label Android & iOS Customer App (Ola/Uber jaisa instant booking aur live GPS tracking), "
                "2. Driver Partner App (OTP verification aur earnings wallet ke saath), "
                "3. Powerful Admin Web Dispatch Panel jahan se aap automated ride assigning aur live fleet track kar sakte hain. "
                "Aapki fleet me lagbhag kitni gaadiyan hain, taaki main aapko best pricing bata sakun?"
            )
        elif "travel" in st or "package" in st:
            return (
                "Hamara Travel & Tourism Package CRM tour operators ke liye best platform hai! Isme aapko milta hai: "
                "1. 2-minute me professional PDF Itinerary Builder, "
                "2. Hotel & Flight package inventory management, "
                "3. Customer Lead CRM jo WhatsApp se connected rehta hai, aur "
                "4. Online Payment Gateway jisse customers aasaani se advance deposit kar sakein. "
                "Aap domestic packages zyada sell karte hain ya international?"
            )
        else:
            return (
                "Hamare Complete Travel & Mobility Suite me aapko Cab Fleet Dispatch aur Travel Package CRM dono milte hain ek hi dashboard me! "
                "Aapke customers ek hi app se airport taxi bhi book kar sakte hain aur Shimla, Goa ya Dubai ka complete holiday package bhi. "
                "Kya aap iska ek live 15-minute screen demo dekhna chahenge?"
            )

    @llm.ai_callable(description="Calculate instant SaaS subscription pricing and setup quotation for Cab Dispatch or Travel Package software.")
    async def calculate_software_pricing(
        self,
        tier: Annotated[str, "Plan tier: 'starter' (1-20 cabs/agents), 'growth' (21-100 cabs), 'enterprise' (unlimited)"] = "growth",
        fleet_or_agent_size: Annotated[int, "Number of cabs in fleet or travel agents in team"] = 25,
    ) -> str:
        self._ensure_sales_session()
        tier_clean = tier.lower().strip()

        if "starter" in tier_clean or fleet_or_agent_size <= 20:
            setup_fee = 14999
            monthly_saas = 2999
            plan_name = "Starter Plan (Upto 20 Fleet/Agents)"
        elif "enterprise" in tier_clean or fleet_or_agent_size > 100:
            setup_fee = 49999
            monthly_saas = 9999
            plan_name = "Enterprise Plan (Unlimited Fleet & Custom Domain)"
        else:
            setup_fee = 24999
            monthly_saas = 4999
            plan_name = "Growth Plan (Upto 100 Cabs/Agents)"

        self.session_data["software_lead"]["quoted_price"] = {
            "tier": plan_name,
            "setupFee": setup_fee,
            "monthlySaas": monthly_saas,
            "fleetSize": fleet_or_agent_size,
        }
        self.record_tool_invocation("calculate_software_pricing", {"plan": plan_name, "setup": setup_fee, "monthly": monthly_saas})

        return (
            f"Aapke business size ({fleet_or_agent_size} vehicles/agents) ke liye hamara '{plan_name}' sabse profitable rahega. "
            f"Isme one-time white-label branding aur setup cost sirf Rs. {setup_fee:,} hai, aur monthly cloud server & support charge Rs. {monthly_saas:,} per month hai. "
            "Isme Google Maps API optimization aur 24x7 technical support bhi included hai. Kya main iska quotation WhatsApp kar doon?"
        )

    @llm.ai_callable(description="Schedule a 1-on-1 live screen demo with the product technical consulting team.")
    async def schedule_software_demo(
        self,
        client_name: Annotated[str, "Client full name or business owner name"],
        business_name: Annotated[str, "Name of travel agency or cab fleet company"],
        preferred_slot: Annotated[str, "Preferred day/time (e.g. 'Tomorrow 3 PM', 'Monday morning')"],
        phone_number: Annotated[str, "Contact phone number for Google Meet / Zoom invite"],
    ) -> str:
        self._ensure_sales_session()
        lead = self.session_data["software_lead"]
        lead["client_name"] = client_name
        lead["business_name"] = business_name
        lead["phone_number"] = phone_number
        lead["demo_scheduled"] = {
            "slot": preferred_slot,
            "bookedAt": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.record_tool_invocation("schedule_software_demo", {"client": client_name, "business": business_name, "slot": preferred_slot})

        return (
            f"Bahut badhiya {client_name} ji! Aapka '{business_name}' ke liye live software demo {preferred_slot} ke liye schedule kar diya gaya hai. "
            f"Hamari technical sales team aapko {phone_number} par calendar invite aur Google Meet link share karegi. "
            "Aap live demo me apne hisaab se customize features bhi discuss kar sakte hain."
        )

    @llm.ai_callable(description="Send product brochure, feature matrix, and pricing rate-card to caller via WhatsApp or Email.")
    async def send_brochure_and_rate_card(
        self,
        solution_name: Annotated[str, "Solution name: 'Cab Booking Software', 'Travel Package CRM', or 'Complete Mobility Suite'"] = "Cab Booking Software",
        delivery_channel: Annotated[str, "Channel: 'whatsapp' or 'email'"] = "whatsapp",
    ) -> str:
        self._ensure_sales_session()
        self.session_data["software_lead"]["brochure_sent"] = True
        self.record_tool_invocation("send_brochure_and_rate_card", {"solution": solution_name, "channel": delivery_channel})

        return (
            f"Maine {solution_name} ka detailed PDF brochure, client case studies aur complete feature rate-card aapke {delivery_channel} par send kar diya hai! "
            "Aap use check kar sakte hain, aur koi bhi doubt ho to mujhse pooch sakte hain."
        )

    @llm.ai_callable(description="Switch call persona or conversation mode dynamically between Cab Booking and Software Sales.")
    async def switch_call_persona(
        self,
        target_persona: Annotated[str, "Target persona: 'cab_booking' (to book a ride) or 'software_sales' (to buy the software/system)"],
        reason: Annotated[str, "Reason for switching (e.g. 'caller wants to buy software', 'caller wants to book a personal taxi')"] = "user_intent_changed",
    ) -> str:
        logger.info(f"🔄 [SalesTool] switch_call_persona: to '{target_persona}', reason='{reason}'")
        self.session_data["active_persona_override"] = target_persona
        self.record_tool_invocation("switch_call_persona", {"target": target_persona, "reason": reason})

        if "cab" in target_persona.lower():
            return (
                "Bilkul! Chaliye ab main aapki taxi booking me madad karti hoon. "
                "Aapko kahan se kahan ke liye cab chahiye, aur kab travel karna hai?"
            )
        else:
            return (
                "Bilkul ji! Main hamare Cab Booking aur Travel Package Software platform ki poori jaankari deti hoon. "
                "Aap apna khud ka cab business ya travel agency chalana chahte hain?"
            )
