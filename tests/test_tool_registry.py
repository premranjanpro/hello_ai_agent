"""
test_tool_registry.py - Comprehensive Unit & Integration Tests for Modular Tool Registry.
"""

import asyncio
import os
import sys

# Add ai-agent to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from toolchain.registry import ToolRegistry
from toolchain.base import BaseToolContext


async def run_tests():
    print("==================================================")
    print("🚀 Running AI Tool Registry & Scalability Tests...")
    print("==================================================")

    # ----------------------------------------------------
    # Test 1: Common Tools present for a generic persona
    # ----------------------------------------------------
    ctx_general = ToolRegistry.create_context(
        persona_id="persona_role_general",
        call_session_id="call_test_001",
        user_id="user_123",
        language="hinglish"
    )
    assert isinstance(ctx_general, BaseToolContext)
    assert hasattr(ctx_general, "disconnect_call")
    assert hasattr(ctx_general, "check_wallet_balance")
    assert hasattr(ctx_general, "set_call_language")
    assert hasattr(ctx_general, "adjust_speaking_speed")
    assert hasattr(ctx_general, "repeat_last_message")
    assert hasattr(ctx_general, "transfer_to_human_agent")
    assert hasattr(ctx_general, "send_sms_whatsapp_summary")
    assert hasattr(ctx_general, "report_call_issue")
    assert hasattr(ctx_general, "verify_caller_identity")
    print("✅ Test 1: All 10 Common Tools successfully attached to generic persona.")

    # ----------------------------------------------------
    # Test 2: Persona Isolation - Cab Booking Tools
    # ----------------------------------------------------
    ctx_cab = ToolRegistry.create_context(
        persona_id="persona_role_cab_booking",
        call_session_id="call_cab_001",
        user_id="user_cab_999",
        language="hindi"
    )
    # Cab tools should be present
    assert hasattr(ctx_cab, "estimate_cab_fare")
    assert hasattr(ctx_cab, "book_cab_ride")
    assert hasattr(ctx_cab, "track_driver_eta")
    # HR tools should NOT be present on cab context
    assert not hasattr(ctx_cab, "save_hr_candidate_evaluation")
    print("✅ Test 2: Cab Booking tools isolated correctly.")

    # ----------------------------------------------------
    # Test 3: Persona Isolation - Parents Care Tools
    # ----------------------------------------------------
    ctx_care = ToolRegistry.create_context(
        persona_id="persona_role_parents_care",
        call_session_id="call_care_001",
        user_id="user_care_888",
    )
    assert hasattr(ctx_care, "trigger_parent_emergency_alert")
    assert hasattr(ctx_care, "set_medicine_reminder")
    assert not hasattr(ctx_care, "book_cab_ride")
    print("✅ Test 3: Parents Care tools isolated correctly.")

    # ----------------------------------------------------
    # Test 4: Tool Execution & Session State Tracking
    # ----------------------------------------------------
    fare_res = await ctx_cab.estimate_cab_fare(
        pickup_location="Noida Sector 62",
        drop_location="Delhi Airport T3",
        cab_type="sedan"
    )
    assert "estimated fare" in fare_res.lower()
    assert ctx_cab.session_data["fare_estimate"] is not None
    print(f"✅ Test 4A: Fare estimation executed -> {fare_res[:60]}...")

    book_res = await ctx_cab.book_cab_ride(
        pickup_location="Noida Sector 62",
        drop_location="Delhi Airport T3",
        cab_type="sedan",
        passenger_name="Rahul"
    )
    assert "confirm ho gayi" in book_res.lower()
    assert ctx_cab.session_data["cab_booking"] is not None
    print(f"✅ Test 4B: Ride confirmation executed -> {book_res[:60]}...")

    # Structured payload generation
    payload = ctx_cab.get_final_structured_payload("persona_role_cab_booking")
    assert payload is not None
    assert payload["dataType"] == "cab_booking"
    print(f"✅ Test 4C: Structured payload compiled -> {payload['summary'][:70]}...")

    # ----------------------------------------------------
    # Test 5: Call Disconnect Execution
    # ----------------------------------------------------
    disco_res = await ctx_cab.disconnect_call(reason="user_finished")
    assert ctx_cab.disconnect_requested is True
    print(f"✅ Test 5: Disconnect tool triggered -> '{disco_res}' (disconnect_requested={ctx_cab.disconnect_requested})")

    # ----------------------------------------------------
    # Test 6: Wallet Balance Check Tool
    # ----------------------------------------------------
    wallet_res = await ctx_cab.check_wallet_balance()
    assert "wallet balance" in wallet_res.lower()
    print(f"✅ Test 6: Wallet balance check tool executed -> '{wallet_res}'")

    # ----------------------------------------------------
    # Test 7: Schedule Callback Request Tool
    # ----------------------------------------------------
    cb_res = await ctx_general.schedule_callback_request(delay_minutes=30, preferred_time="aadhe ghante baad", disconnect_now=True)
    assert "aadhe ghante baad" in cb_res
    assert ctx_general.disconnect_pending is True
    assert ctx_general.session_data["callback_request"]["delayMinutes"] == 30
    print(f"✅ Test 7: Schedule callback request tool executed -> '{cb_res}'")

    # ----------------------------------------------------
    # Test 8: Software Sales Persona & Dynamic Switching
    # ----------------------------------------------------
    ctx_sales = ToolRegistry.create_context(
        persona_id="persona_role_software_sales",
        call_session_id="call_sales_001",
        user_id="lead_101",
        language="hinglish"
    )
    assert hasattr(ctx_sales, "pitch_software_features")
    assert hasattr(ctx_sales, "calculate_software_pricing")
    assert hasattr(ctx_sales, "schedule_software_demo")
    assert hasattr(ctx_sales, "switch_call_persona")

    pitch_res = await ctx_sales.pitch_software_features(solution_type="cab_dispatch")
    assert "Cab Dispatch Software" in pitch_res
    print(f"✅ Test 8A: Software Sales pitch executed -> {pitch_res[:65]}...")

    price_res = await ctx_sales.calculate_software_pricing(tier="growth", fleet_or_agent_size=35)
    assert "Growth Plan" in price_res
    assert ctx_sales.session_data["software_lead"]["quoted_price"]["monthlySaas"] == 4999
    print(f"✅ Test 8B: Software pricing calculated -> {price_res[:65]}...")

    demo_res = await ctx_sales.schedule_software_demo(
        client_name="Vikram Singh",
        business_name="Royal Cabs & Travels",
        preferred_slot="Tomorrow 3 PM",
        phone_number="9876543210"
    )
    assert "Royal Cabs & Travels" in demo_res
    print(f"✅ Test 8C: Software demo booked -> {demo_res[:65]}...")

    switch_res = await ctx_sales.switch_call_persona(target_persona="cab_booking")
    assert "taxi booking" in switch_res
    print(f"✅ Test 8D: Dynamic persona switch executed -> {switch_res}")

    # ----------------------------------------------------
    # Test 9: Kids Game Persona & 10s Quiz Engine
    # ----------------------------------------------------
    ctx_game = ToolRegistry.create_context(
        persona_id="persona_role_kids_game",
        call_session_id="call_game_001",
        user_id="kid_202",
        language="hindi"
    )
    assert hasattr(ctx_game, "ask_next_quiz_question")
    assert hasattr(ctx_game, "submit_quiz_answer")
    assert hasattr(ctx_game, "give_quiz_hint")
    assert hasattr(ctx_game, "get_game_score")

    q_res = await ctx_game.ask_next_quiz_question(category="Animals")
    assert "10 second" in q_res or "Option" in q_res
    curr_q = ctx_game.session_data["game_session"]["current_question"]
    assert curr_q is not None
    print(f"✅ Test 9A: Quiz question asked with 10s countdown -> '{curr_q['question']}'")

    # Submit correct answer for the active question
    correct_opt_text = curr_q["options"][curr_q["correct_index"]]
    ans_res = await ctx_game.submit_quiz_answer(selected_option=correct_opt_text)
    assert ctx_game.session_data["game_session"]["score"] >= 10
    assert ctx_game.session_data["game_session"]["stars"] >= 1
    print(f"✅ Test 9B: Answer validated & scored -> {ans_res[:65]}...")

    score_res = await ctx_game.get_game_score()
    assert "score" in score_res.lower()
    print(f"✅ Test 9C: Game score reported -> {score_res}")

    print("\n==================================================")
    print("🎉 ALL TESTS PASSED! Modular Toolchain Verified!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
