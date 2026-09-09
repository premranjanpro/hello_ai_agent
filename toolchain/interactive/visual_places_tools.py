"""
visual_places_tools.py - Dedicated Multimodal Visual Monuments & Famous Places Toolchain.

Enables the AI caller to say 'Taj Mahal ka photo dikhao', 'Delhi ke India Gate dikhao', 'Mumbai Marine Drive dikhao'.
Pops up a high-resolution media card in the in-call bottom sheet with verified photos and quick facts,
which then cleanly auto-dismisses after 12 seconds.
"""

import logging
from typing import Annotated, Dict, Any, List
from livekit.agents import llm

logger = logging.getLogger("toolchain.interactive.visual_places")

# Verified high-resolution imagery and architectural trivia for major Indian monuments
FAMOUS_PLACES_CATALOG: Dict[str, Dict[str, Any]] = {
    "taj_mahal": {
        "keywords": ["taj mahal", "tajmahal", "mumtaz", "agra wonder"],
        "title": "Taj Mahal",
        "city": "Agra, Uttar Pradesh",
        "badge": "NEW 7 WONDERS OF THE WORLD",
        "image_url": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=900&auto=format&fit=crop&q=80",
        "caption": "Mughal Emperor Shah Jahan dwara banwaya gaya safed sangmarmar ka azeem maqbara.",
        "quick_facts": [
            "Location: Agra, Yamuna Nadi ke kinare",
            "Nirman Varsh: 1632 - 1653 AD",
            "Architectural Wonder: UNESCO World Heritage Site",
            "Specialty: Makrana ka pure White Marble"
        ],
        "speech": "Ye dekhiye aapki screen par azeem-o-shaan Taj Mahal ki tasveer! Shah Jahan ne ise apni begum Mumtaz Mahal ki yaad me Agra me Yamuna nadi ke kinare banwaya tha."
    },
    "agra_fort": {
        "keywords": ["agra fort", "agra ka qila", "red fort agra"],
        "title": "Agra Fort (Lal Qila Agra)",
        "city": "Agra, Uttar Pradesh",
        "badge": "UNESCO HERITAGE SITE",
        "image_url": "https://images.unsplash.com/photo-1598324789736-4861f89564a0?w=900&auto=format&fit=crop&q=80",
        "caption": "Mughal shaashan ka mukhy nivas sthal aur etihasik laal balua patthar ka dilli darwaza qila.",
        "quick_facts": [
            "Location: Agra, Uttar Pradesh",
            "Nirmata: Mughal Samrat Akbar (1565 AD)",
            "Prominent Structures: Sheesh Mahal, Diwan-i-Khas",
            "Distance: Taj Mahal se keval 2.5 km door"
        ],
        "speech": "Ye lijiye, aapke screen par hai Agra ka Lal Qila! Ise Akbar ne banwaya tha aur ye Mughal hukumat ka pramukh kendra tha."
    },
    "india_gate": {
        "keywords": ["india gate", "delhi gate", "amar jawan jyoti"],
        "title": "India Gate",
        "city": "New Delhi",
        "badge": "NATIONAL WAR MEMORIAL",
        "image_url": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=900&auto=format&fit=crop&q=80",
        "caption": "Pehle Vishva Yudh me shaheed hue 84,000 veer sainiko ki yaad me bana smarak.",
        "quick_facts": [
            "Location: Kartavya Path, New Delhi",
            "Height: 42 Metres",
            "Architect: Sir Edwin Lutyens (1931)",
            "Significance: Amar Jawan Jyoti"
        ],
        "speech": "Ye dekhiye New Delhi ka mashhoor India Gate! Ise Sir Edwin Lutyens ne design kiya tha aur ye hamare veer sainiko ke samman me bana hai."
    },
    "red_fort": {
        "keywords": ["red fort", "lal qila", "lal quila delhi"],
        "title": "Red Fort (Lal Qila)",
        "city": "Old Delhi",
        "badge": "NATIONAL SYMBOL",
        "image_url": "https://images.unsplash.com/photo-1592635196078-9fe3d54f2377?w=900&auto=format&fit=crop&q=80",
        "caption": "Swatantrata Divas par Rashtriya Dhwaj tiranga phahrane ka etihasik sthal.",
        "quick_facts": [
            "Location: Netaji Subhash Marg, Chandni Chowk, Delhi",
            "Built by: Shah Jahan (1648 AD)",
            "Material: Red Sandstone",
            "Event: Pradhan Mantri ka 15 August Bhashan"
        ],
        "speech": "Ye raha Delhi ka shaan-daar Lal Qila! Har saal 15 August ko Pradhan Mantri yahin se tiranga phahrate hain."
    },
    "qutub_minar": {
        "keywords": ["qutub minar", "qutab minar", "kutub minar"],
        "title": "Qutub Minar",
        "city": "Mehrauli, South Delhi",
        "badge": "TALLEST BRICK MINARET",
        "image_url": "https://images.unsplash.com/photo-1548013146-72479768bada?w=900&auto=format&fit=crop&q=80",
        "caption": "Duniya ki sabse unchi eent (brick) se bani minar, unchai 72.5 metre.",
        "quick_facts": [
            "Height: 72.5 Metres (238 feet)",
            "Started by: Qutb-ud-din Aibak (1199 AD)",
            "Completed by: Iltutmish",
            "Attraction: 1600 saal purana Iron Pillar"
        ],
        "speech": "Ye lijiye Qutub Minar ki tasveer! Ye 72.5 metre unchi duniya ki sabse unchi eenton se bani minar hai."
    },
    "gateway_of_india": {
        "keywords": ["gateway of india", "mumbai gateway", "gateway mumbai"],
        "title": "Gateway of India",
        "city": "Mumbai, Maharashtra",
        "badge": "ICON OF MUMBAI",
        "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=900&auto=format&fit=crop&q=80",
        "caption": "Arab Saagar ke tat par sthit Mumbai ka sabse aakarshak etihasik dwar.",
        "quick_facts": [
            "Location: Colaba, Mumbai Waterfront",
            "Built in: 1924 (King George V aagman)",
            "Adjacent: Famous Taj Mahal Palace Hotel",
            "Style: Indo-Saracenic Architecture"
        ],
        "speech": "Ye dekhiye Mumbai ka mashhoor Gateway of India! Arab Saagar ke tat par bana ye dwar Mumbai ki sabse badi pehchan hai."
    },
    "marine_drive": {
        "keywords": ["marine drive", "queen necklace", "nariman point marine drive", "mumbai beach"],
        "title": "Marine Drive (Queen's Necklace)",
        "city": "South Mumbai, Maharashtra",
        "badge": "QUEEN'S NECKLACE",
        "image_url": "https://images.unsplash.com/photo-1566552881560-0be862a7c445?w=900&auto=format&fit=crop&q=80",
        "caption": "Raat me motiyo ki mala jaisa chamakne wala 3.6 km lamba coastal boulevard promenade.",
        "quick_facts": [
            "Stretch: 3.6 Kilometres C-shaped Promenade",
            "Connects: Nariman Point to Babulnath / Malabar Hill",
            "Famous for: Sunset view, sea breeze & night lights",
            "UNESCO: Art Deco Ensemble"
        ],
        "speech": "Ye raha Mumbai ka khoobsurat Marine Drive! Raat ke samay street lights ki wajah se ye bilkul Queen's Necklace ki tarah chamakta hai."
    },
    "hawa_mahal": {
        "keywords": ["hawa mahal", "jaipur pink city", "palace of winds"],
        "title": "Hawa Mahal (Palace of Winds)",
        "city": "Jaipur, Rajasthan",
        "badge": "PINK CITY JEWEL",
        "image_url": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=900&auto=format&fit=crop&q=80",
        "caption": "953 jharokhon (windows) se sajji gulabi nagri Jaipur ki anoothi imarat.",
        "quick_facts": [
            "Built by: Maharaja Sawai Pratap Singh (1799)",
            "Windows: 953 Intricately carved Jharokhas",
            "Architect: Lal Chand Ustad",
            "Purpose: Royal ladies ke street dekhne hetu"
        ],
        "speech": "Ye dekhiye Jaipur ka vishva-prasiddh Hawa Mahal! Isme 953 jharokhe hain jahan se hamesha thandi hawa aati rehti hai."
    },
    "golden_temple": {
        "keywords": ["golden temple", "harmandir sahib", "amritsar gurudwara", "swarna mandir"],
        "title": "Golden Temple (Sri Harmandir Sahib)",
        "city": "Amritsar, Punjab",
        "badge": "SPIRITUAL SANCTUARY",
        "image_url": "https://images.unsplash.com/photo-1590402494682-cd3fb53b1f70?w=900&auto=format&fit=crop&q=80",
        "caption": "Shuddh sone se mandit amrit sarovar ke beech sthit pavitra dharamik sthal.",
        "quick_facts": [
            "Location: Amritsar, Punjab",
            "Founded by: Guru Ram Das Ji (1577)",
            "Specialty: 24/7 Free Mega Langar (community kitchen)",
            "Atmosphere: Sarovar surrounded by divine peace"
        ],
        "speech": "Ye dekhiye Amritsar ka pavitra Golden Temple! Ye shuddh sone se sajjit hai aur yahan ka shaant vatavaran mann ko moh leta hai."
    }
}


class VisualPlacesToolsMixin:
    """Multimodal visual display toolchain for monuments and famous places."""

    @llm.ai_callable(description="Show a high-resolution photograph and quick facts of a famous Indian place or monument (Taj Mahal, India Gate, Red Fort, Qutub Minar, Gateway of India, Marine Drive, Hawa Mahal, Golden Temple) in the in-call bottom sheet. The sheet automatically auto-dismisses after 12 seconds.")
    async def show_famous_place(
        self,
        place_name: Annotated[str, "Name of the place or monument, e.g. 'Taj Mahal', 'India Gate', 'Marine Drive', 'Agra Fort', 'Hawa Mahal', 'Golden Temple'"],
        city: Annotated[str, "City name if specified by user, e.g. 'Agra', 'Delhi', 'Mumbai', 'Jaipur', 'Amritsar'"] = "",
    ) -> str:
        logger.info(f"🏛️ [VisualPlaces] show_famous_place: place='{place_name}', city='{city}'")
        self.record_tool_invocation("show_famous_place", {"place_name": place_name, "city": city})

        clean_query = f"{place_name} {city}".lower().strip()

        # Match monument from catalog
        matched_item = None
        for key, item in FAMOUS_PLACES_CATALOG.items():
            if any(kw in clean_query for kw in item["keywords"]):
                matched_item = item
                break

        # Fallback to Taj Mahal if general "monument" or not found
        if not matched_item:
            if "mumbai" in clean_query:
                matched_item = FAMOUS_PLACES_CATALOG["gateway_of_india"]
            elif "delhi" in clean_query:
                matched_item = FAMOUS_PLACES_CATALOG["india_gate"]
            elif "agra" in clean_query:
                matched_item = FAMOUS_PLACES_CATALOG["taj_mahal"]
            else:
                matched_item = FAMOUS_PLACES_CATALOG["taj_mahal"]

        # Build declarative media_card payload
        sheet_payload = {
            "action": "open",
            "sheet_id": f"place_{matched_item['title'].lower().replace(' ', '_')}",
            "component": "media_card",
            "title": matched_item["title"],
            "subtitle": matched_item["city"],
            "badge": matched_item["badge"],
            "auto_dismiss_seconds": 12,  # Auto-dismisses cleanly after 12s as requested
            "media": {
                "image_url": matched_item["image_url"],
                "caption": matched_item["caption"],
                "aspect_ratio": 1.5
            },
            "quick_facts": matched_item["quick_facts"],
            "speech_hint": matched_item["speech"]
        }

        # Emit to app screen
        if hasattr(self, "emit_interactive_sheet"):
            await self.emit_interactive_sheet(sheet_payload)

        return matched_item["speech"]
