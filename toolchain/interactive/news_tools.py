"""
news_tools.py - Dedicated Today's News & Interactive News Card Toolchain.

Enables the caller to say 'aaj ka news btao', 'sports news sunao', 'tech news kya hai'.
Pops up an interactive news card bottom sheet with headlines and highlights, reads them out loud,
and automatically auto-dismisses after 15 seconds.
"""

import time
import logging
from typing import Annotated, Dict, Any, List
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.news")

# Curated daily headlines and bullet highlights categorized by domain
NEWS_BULLETIN: Dict[str, Dict[str, Any]] = {
    "top": {
        "title": "Aaj Ki Taaza Mukhya Khabrein",
        "category_badge": "TOP HEADLINES",
        "headlines": [
            "Bharat ne Green Energy me naya kirtiman banaya: Solar aur Wind power generation me 15% ki badhotari darj ki gayi.",
            "Indian Railways ne naye Vande Bharat express routes shuru kiye, yatra ka samay lagbhag 2 ghante kam hua.",
            "ISRO ke naye space exploration mission ki teyariyaan tez, next-generation satellites ki launch date declare."
        ],
        "speech": "Aaj ki mukhya khabrein aapki screen par aa chuki hain! Pehli badi khabar hai ki Bharat ne green energy me naya record banaya hai. Saath hi naye Vande Bharat trains aur ISRO ke naye space mission ki teyari zor-shor se chal rahi hai."
    },
    "tech": {
        "title": "Technology & AI News",
        "category_badge": "TECH UPDATE",
        "headlines": [
            "Next-Gen Real-Time Voice AI Agent launch: Bilkul human jaisi natural awaaz aur zero lag conversation.",
            "Telecom companies ne naye 5G Advanced aur 6G testing labs Bharat me establish kiye.",
            "Smartphone market me ultra-fast charging aur AI camera sensors ka naya daur shuru."
        ],
        "speech": "Technology jagat ki taaza khabrein dekhiye! Real-Time Voice AI technology me bada breakthrough hua hai, aur 5G Advanced ke baad ab Bharat me naye 6G testing labs tezi se taiyar ho rahe hain."
    },
    "sports": {
        "title": "Sports & Cricket Highlights",
        "category_badge": "SPORTS BUZZ",
        "headlines": [
            "Indian Cricket Team ka naya squad announce, aane wale tournament ke liye young players ko bada mauka mila.",
            "International Athletics Championship me Bharat ke javelin aur track athletes ne shandar pradarshan kiya.",
            "Premier League aur Champions League me high-voltage matches me naye records bane."
        ],
        "speech": "Sports ki badi khabrein! Indian Cricket Team ka aane wale matches ke liye shandar squad tay ho chuka hai, aur hamare track and field athletes ne international level par tiranga lehrane me badi safalta hasil ki hai."
    },
    "entertainment": {
        "title": "Bollywood & Entertainment",
        "category_badge": "ENTERTAINMENT",
        "headlines": [
            "Weekend Box Office par naye action thriller ne record opening ki, darshako ki bhari bheed.",
            "OTT platforms par naye crime thriller aur family drama shows trending chart me top par pahunche.",
            "Music world me naya soulful track YouTube aur streaming apps par 24 ghante me viral."
        ],
        "speech": "Entertainment news me Box Office par nayi film ne dhoom macha di hai, aur OTT par nayi web series ne darshako ka dil jeet liya hai!"
    }
}


class LiveNewsToolsMixin:
    """Live and daily news bottom sheet display toolchain."""

    @llm.ai_callable(description="Show and read today's latest news headlines (Top news, Tech, Sports, Entertainment) in the in-call bottom sheet. The sheet automatically auto-dismisses after 15 seconds.")
    async def show_todays_news(
        self,
        category: Annotated[str, "News category: 'top' (mukhya khabrein), 'tech' (technology), 'sports' (khel), or 'entertainment' (bollywood)"] = "top",
    ) -> str:
        logger.info(f"📰 [NewsTool] show_todays_news: category='{category}'")
        self.record_tool_invocation("show_todays_news", {"category": category})

        cat_clean = category.lower().strip()
        if "tech" in cat_clean or "ai" in cat_clean or "mobile" in cat_clean:
            key = "tech"
        elif "sport" in cat_clean or "cric" in cat_clean or "khel" in cat_clean:
            key = "sports"
        elif "bolly" in cat_clean or "movie" in cat_clean or "film" in cat_clean or "ent" in cat_clean:
            key = "entertainment"
        else:
            key = "top"

        news_item = NEWS_BULLETIN[key]
        today_date = time.strftime("%d %B %Y")

        sheet_payload = {
            "action": "open",
            "sheet_id": f"news_{key}_{int(time.time())}",
            "component": "news",
            "title": news_item["title"],
            "subtitle": f"Live Bulletin • {today_date}",
            "badge": news_item["category_badge"],
            "auto_dismiss_seconds": 15,  # Auto-dismisses after 15 seconds
            "quick_facts": news_item["headlines"],
            "speech_hint": news_item["speech"]
        }

        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return news_item["speech"]
