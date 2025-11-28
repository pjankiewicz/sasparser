"""Handler registry and handler imports."""

from __future__ import annotations
from typing import TYPE_CHECKING

from .base import BaseHandler, ParseContext

if TYPE_CHECKING:
    from ..core.tokens import Token


class HandlerRegistry:
    """Registry for SAS construct handlers."""

    _handlers: list[type[BaseHandler]] = []
    _initialized: bool = False

    @classmethod
    def register(cls, handler_class: type[BaseHandler]) -> type[BaseHandler]:
        """Register a handler class."""
        if handler_class not in cls._handlers:
            cls._handlers.append(handler_class)
        return handler_class

    @classmethod
    def find_handler(cls, tokens: list[Token], pos: int) -> BaseHandler | None:
        """Find a handler that can process tokens at position."""
        cls._ensure_initialized()
        for handler_class in cls._handlers:
            if handler_class.can_handle(tokens, pos):
                return handler_class()
        return None

    @classmethod
    def get_all_handlers(cls) -> list[type[BaseHandler]]:
        """Get all registered handlers."""
        cls._ensure_initialized()
        return cls._handlers.copy()

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure handlers are imported and registered."""
        if cls._initialized:
            return
        cls._initialized = True
        # Import handlers to trigger registration
        from . import data_step  # noqa: F401
        from . import proc_sql  # noqa: F401
        from . import proc_sort  # noqa: F401
        from . import proc_means  # noqa: F401
        from . import proc_freq  # noqa: F401
        from . import proc_print  # noqa: F401
        from . import libname  # noqa: F401
        from . import macro  # noqa: F401


def register(handler_class: type[BaseHandler]) -> type[BaseHandler]:
    """Decorator to register a handler."""
    return HandlerRegistry.register(handler_class)


__all__ = ["HandlerRegistry", "BaseHandler", "ParseContext", "register"]
