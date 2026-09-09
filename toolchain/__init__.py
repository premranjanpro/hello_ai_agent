"""
toolchain - Modular, Scalable In-Memory FunctionContext for LiveKit AI Voice Calls.
Separates Universal Common Tools from Role-Specific Domain Tools.
"""

from toolchain.base import BaseToolContext
from toolchain.registry import ToolRegistry

# Alias for backward compatibility
SessionData = BaseToolContext

__all__ = ["BaseToolContext", "ToolRegistry", "SessionData"]
