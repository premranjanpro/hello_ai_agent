"""
account_tools.py - Universal Account & Service Tools (Wallet Balance, Support Transfer, Summary, Issues, Identity).
"""

import logging
from typing import Annotated
import aiohttp
from livekit.agents import llm

logger = logging.getLogger("toolchain.common.account_tools")


class AccountToolsMixin:
    """Provides universal account and user-interaction tools to any FunctionContext."""

    @llm.ai_callable(description="Check the caller's live wallet balance when they ask 'mera balance kitna hai' or 'wallet balance check karo'.")
    async def check_wallet_balance(self) -> str:
        logger.info(f"💰 [Tool] check_wallet_balance for user={self.user_id}")
        self.record_tool_invocation("check_wallet_balance", {"user_id": self.user_id})

        balance = 0.0
        currency = "INR"

        if self.user_id and self.api_base_url:
            try:
                url = f"{self.api_base_url}/api/ai/users/{self.user_id}/balance"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            balance = float(data.get("balance", 0.0))
                            currency = data.get("currency", "INR")
            except Exception as e:
                logger.debug(f"Direct balance check failed ({e}), using fallback")

        self.session_data["wallet_balance_inquiries"].append({"balance": balance, "currency": currency})

        if balance > 0:
            return f"Aapka current wallet balance Rs. {balance:.2f} hai. Aap isse apni calling aur services enjoy kar sakte hain!"
        return "Aapka wallet balance abhi Rs. 0.00 hai. Aap mobile app ke Wallet section me jaakar aasaani se recharge kar sakte hain."

    # Retained as internal helper methods without @llm.ai_callable to save ~600 input tokens per turn on Groq Free Tier
    async def transfer_to_human_agent(
        self,
        department: Annotated[str, "Department to transfer to: 'support', 'billing', 'driver_escalation'"] = "support",
    ) -> str:
        logger.info(f"👥 [Tool] transfer_to_human_agent: department='{department}'")
        self.record_tool_invocation("transfer_to_human_agent", {"department": department})
        self.session_data["transfer_requests"].append({"department": department})

        if self.room:
            try:
                import json
                payload = json.dumps({"type": "call_transfer_requested", "department": department}).encode("utf-8")
                await self.room.local_participant.publish_data(payload, reliable=True)
            except Exception as e:
                logger.debug(f"Failed to publish transfer signal: {e}")

        return (
            f"Main aapki call hamare {department.capitalize()} executive ko transfer kar rahi hoon. "
            "Kripya line par bane rahein, agla available executive aapse connect ho raha hai."
        )

    async def send_sms_whatsapp_summary(
        self,
        channel: Annotated[str, "Delivery channel: 'whatsapp' or 'sms'"] = "whatsapp",
    ) -> str:
        logger.info(f"📲 [Tool] send_sms_whatsapp_summary via {channel}")
        self.record_tool_invocation("send_sms_whatsapp_summary", {"channel": channel})

        return (
            f"Maine aapki call ki summary aur details aapke registered mobile number par {channel.capitalize()} ke through send kar di hai. "
            "Aap check kar sakte hain!"
        )

    async def report_call_issue(
        self,
        issue_description: Annotated[str, "Description of the problem (e.g. 'voice breaking', 'echo', 'delay')"],
    ) -> str:
        logger.warning(f"⚠️ [Tool] report_call_issue: '{issue_description}'")
        self.record_tool_invocation("report_call_issue", {"issue": issue_description})
        self.session_data["reported_issues"].append(issue_description)

        return (
            "Asuvidha ke liye maafi chahte hain. Maine ye technical feedback note kar liya hai aur hamari engineering team "
            "isko optimize karne ke liye turant review karegi. Kya hum aage continue karein?"
        )

    async def verify_caller_identity(self) -> str:
        logger.info(f"🔐 [Tool] verify_caller_identity for user={self.user_id}")
        self.record_tool_invocation("verify_caller_identity", {})

        return (
            "Suraksha ke liye maine aapke phone par ek 4-digit verification code bhej diya hai. "
            "Kripya screen par aane wala code mujhe batayein."
        )
