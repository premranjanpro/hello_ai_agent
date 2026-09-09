"""
orchestrator/memory_manager.py - Real-Time and Cross-Session Caller Memory Manager.
Handles caller context fetching, turn history persistence, and compact memory summarization.
"""

import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger("orchestrator.memory")


class MemoryManager:
    """Manages cross-session caller memories, preference tracking, and compaction."""

    def __init__(self, backend_api_url: Optional[str] = None):
        self.backend_api_url = (backend_api_url or os.getenv("HELLO_API_URL", "http://localhost:5063")).rstrip("/")

    async def fetch_caller_memory(self, caller_phone: str, persona_id: str) -> Dict[str, Any]:
        """Fetches persisted caller context from backend API."""
        if not caller_phone:
            return {"memory_summary": "", "total_calls": 0, "caller_name": ""}

        url = f"{self.backend_api_url}/api/caller-memory"
        params = {"phoneNumber": caller_phone, "personaId": persona_id}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=1.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"[MemoryManager] Loaded memory for {caller_phone}: {data.get('memory_summary', '')[:60]}...")
                        return data
        except Exception as e:
            logger.debug(f"[MemoryManager] Could not fetch caller memory: {e}")

        return {"memory_summary": "", "total_calls": 0, "caller_name": ""}

    async def save_caller_memory(
        self,
        caller_phone: str,
        persona_id: str,
        memory_summary: str,
        caller_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Persists updated memory summary for subsequent calls."""
        if not caller_phone or not memory_summary:
            return False

        url = f"{self.backend_api_url}/api/caller-memory"
        payload = {
            "phoneNumber": caller_phone,
            "personaId": persona_id,
            "memorySummary": memory_summary,
            "callerName": caller_name or "",
            "metadata": metadata or {},
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                    if resp.status in (200, 201, 204):
                        logger.info(f"[MemoryManager] Saved memory for {caller_phone}")
                        return True
        except Exception as e:
            logger.warning(f"[MemoryManager] Failed to save caller memory: {e}")

        return False
