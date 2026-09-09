"""
user_call_tools.py - Dedicated Toolchain for Real User-to-User & Host LiveKit Calls.

Strictly separated from companion/conversational tools.
Handles:
1. Specific user lookup & calling (e.g., 'call @rahul', 'is user ko call lga do').
2. Matchmaking calls by gender/city (e.g., 'delhi ki hot ladki ko call lga do').
3. Caller-consented alternate online host bridging.
4. SignalR incoming call ringing and LiveKit room audio bridging.
"""

import logging
from typing import Annotated
from livekit.agents import llm

logger = logging.getLogger("toolchain.user_calling")


class UserToUserCallToolsMixin:
    """Dedicated User-to-User Calling Toolchain for placing real voice calls to users and hosts."""

    @llm.ai_callable(description="Call a specific registered user or host by their username or display name into this live call room. Used when caller says 'is user ko call lga do', 'rahul ko call lagao', 'call @username'.")
    async def call_specific_user(
        self,
        target_username_or_name: Annotated[str, "The username or display name of the user to call, e.g. 'rahul', 'priya', '@nikita'"],
    ) -> str:
        logger.info(f"📞 [UserCallTool] call_specific_user: target='{target_username_or_name}'")
        self.record_tool_invocation("call_specific_user", {"target": target_username_or_name})

        room_name = getattr(getattr(self, "room", None), "name", None) or getattr(self, "call_session_id", "call_room")
        api_url = getattr(self, "api_base_url", "http://localhost:5063")
        caller_id = getattr(self, "user_id", "")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "roomName": room_name,
                    "targetUsername": target_username_or_name.strip().lstrip("@"),
                    "callerUserId": caller_id
                }
                async with session.post(f"{api_url}/api/ai/bridge-call", json=payload, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            host_name = data.get("hostUsername", target_username_or_name)
                            host_city = data.get("city", "")
                            city_phrase = f" ({host_city} se)" if host_city else ""
                            return f"Bilkul! Maine @{host_name}{city_phrase} ko call ring kar di hai. Unhe live audio room me connect kiya ja raha hai, bas 2 second line pe rahiye."
                        
                        # Target user found but offline
                        if data.get("targetUserFound") and not data.get("isOnline"):
                            msg = data.get("message", f"Maaf kijiye, @{target_username_or_name} abhi offline hain.")
                            return f"{msg} (INSTRUCTION TO AI: Inform caller they are offline. Ask if they would like to talk to another online host)."

                        # Target user not found
                        if not data.get("targetUserFound"):
                            msg = data.get("message", f"Maaf kijiye, '{target_username_or_name}' naam ka koi user nahi mil paaya.")
                            return f"{msg} (INSTRUCTION TO AI: Inform caller gently that user wasn't found and offer to connect to any online host)."

                        return data.get("message", "User se connect nahi ho paaya.")
        except Exception as e:
            logger.error(f"Error calling specific user: {e}", exc_info=True)

        return f"Maaf kijiye, abhi @{target_username_or_name} se connect karne me technical samasya aa rahi hai. Kya main kisi doosri online host ko connect karoon?"

    @llm.ai_callable(description="Match and connect the caller to a real online girl or boy host by preferences like city, gender, or personality into the current audio call room. Strictly checks real online availability. E.g. 'delhi ki ladki ko call lga do', 'kisi ladki se baat karao'.")
    async def connect_to_matched_host(
        self,
        desired_gender: Annotated[str, "The gender of the person: 'female' (girl/ladki) or 'male' (boy/ladka)"] = "female",
        city: Annotated[str, "The city or location requested by user, e.g. 'Delhi', 'Mumbai', 'Kolkata', 'Pune'"] = "",
        requirement: Annotated[str, "The specific preference or conversation requirement: e.g. 'friendly chat', 'hot ladki', 'Hindi speaking', 'not boring'"] = "friendly chat",
        language: Annotated[str, "The preferred language, e.g. 'Hindi', 'English', 'Bengali', 'Marathi', 'Hinglish'"] = "",
    ) -> str:
        logger.info(f"🤝 [UserCallTool] connect_to_matched_host: gender={desired_gender}, city={city}, requirement={requirement}, lang={language}")
        self.record_tool_invocation("connect_to_matched_host", {"gender": desired_gender, "city": city, "requirement": requirement, "language": language})

        room_name = getattr(getattr(self, "room", None), "name", None) or getattr(self, "call_session_id", "call_room")
        api_url = getattr(self, "api_base_url", "http://localhost:5063")
        gender_label = "ladki" if "fem" in desired_gender.lower() else "ladka"
        caller_id = getattr(self, "user_id", "")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "roomName": room_name,
                    "desiredGender": desired_gender,
                    "requirement": requirement,
                    "city": city,
                    "language": language,
                    "callerUserId": caller_id
                }
                async with session.post(f"{api_url}/api/ai/bridge-call", json=payload, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            host_name = data.get("hostUsername", "User")
                            host_city = data.get("city", "")
                            city_phrase = f" ({host_city} se)" if host_city else ""
                            return f"Great news! Maine aapke liye{city_phrase} @{host_name} ko dhundh liya hai. Unke mobile pe call ring ho rahi hai aur room me bridge kiya ja raha hai, bas 2 second line pe rahiye."
                        
                        elif data.get("alternateFound"):
                            # Store pending alternate host in session for user confirmation
                            self.session_data["pending_alternate_host_id"] = data.get("alternateHostId")
                            self.session_data["pending_alternate_username"] = data.get("alternateUsername")
                            self.session_data["pending_alternate_city"] = data.get("alternateCity")
                            self.session_data["pending_alternate_gender"] = data.get("alternateGender")
                            msg = data.get("message")
                            alt_city = data.get("alternateCity", "doosre shahar")
                            return (
                                f"[STATUS: ALTERNATE_OFFERED] {msg} "
                                f"(INSTRUCTION TO AI: Do NOT say they are from {city}. Honestly tell the user: "
                                f"'{city} ki to abhi online nahi hai, lekin ek {gender_label} ({alt_city} se) online hai. Kya unke sath call laga doon?' "
                                f"If the user says 'haan' / 'yes' / 'laga do', invoke confirm_alternate_bridge immediately!)"
                            )
                        else:
                            msg = data.get("message", f"Maaf kijiye, is samay koi bhi {gender_label} online nahi mil paaye.")
                            return f"{msg} Main yahin hoon aapke saath baat jari rakhne ke liye, bataiye aap kya baat karna chahte hain?"
        except Exception as e:
            logger.error(f"Failed to connect matched host: {e}", exc_info=True)

        city_phrase = f" {city} se" if city else ""
        return f"Maaf kijiye, is samay{city_phrase} koi {gender_label} online nahi mil paaye. Hum aapko jald hi connect karenge!"

    @llm.ai_callable(description="Call this tool when the user says YES / haan / theek hai / laga do to connect with the suggested alternate online host.")
    async def confirm_alternate_bridge(self) -> str:
        logger.info("🤝 [UserCallTool] confirm_alternate_bridge invoked by caller consent.")
        self.record_tool_invocation("confirm_alternate_bridge", {})

        pending_id = self.session_data.get("pending_alternate_host_id")
        alt_name = self.session_data.get("pending_alternate_username", "Host")
        alt_city = self.session_data.get("pending_alternate_city", "")

        if not pending_id:
            return "Kripya bataiye aap kis tarah ke host se judna chahte hain, main dhoondh deti hoon!"

        room_name = getattr(getattr(self, "room", None), "name", None) or getattr(self, "call_session_id", "call_room")
        api_url = getattr(self, "api_base_url", "http://localhost:5063")
        caller_id = getattr(self, "user_id", "")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "roomName": room_name,
                    "confirmedHostId": pending_id,
                    "forceConnectAlternate": True,
                    "callerUserId": caller_id
                }
                async with session.post(f"{api_url}/api/ai/bridge-call", json=payload, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success"):
                            host_name = data.get("hostUsername", alt_name)
                            city_phrase = f" ({alt_city} se)" if alt_city else ""
                            return f"Bilkul! Maine aapko{city_phrase} @{host_name} ke sath connect kar diya hai. Unki ghanti baj rahi hai, bas 2 second line pe rahiye."
        except Exception as e:
            logger.error(f"Failed to confirm bridge call: {e}", exc_info=True)

        return f"Theek hai, main @{alt_name} ko call me connect karne ka alert bhej rahi hoon. Line par rahiye!"
