"""Fixes for bugs in Python 3.5.2's typing module."""

from typing import Any, Type, TYPE_CHECKING

try:
    from typing import ContextManager  # pylint: disable=W0611
except ImportError:
    # typing.ContextManager is missing from Python 3.5. It's available in the
    # pypi package, but installing that won't override the system package. We
    # can fake it (runtime types don't matter). Mypy is aware of
    # typing.ContextManager, so when it is invoked it will use the proper
    # version.
    #
    # See: https://stackoverflow.com/q/44651115/568785

    class _ContextManager:  # pylint: disable=R0903
        def __getitem__(self, index: Any) -> Any:
            return type(object())

    if not TYPE_CHECKING:  # pragma: no cover
        ContextManager = _ContextManager()

# Workaround for a 3.5.2 bug: https://stackoverflow.com/q/49959656/568785
if TYPE_CHECKING:  # pragma: no cover
    BaseExceptionType = Type[BaseException]  # pylint: disable=C0103
else:  # pragma: no cover
    # We don't really care what this is, Type[BaseException] is borked at
    # runtime, so just put something that is a type (won't error)
    BaseExceptionType = bool
