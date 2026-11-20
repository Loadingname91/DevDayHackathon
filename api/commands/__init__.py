"""The command service (backend.md §5): the one write path for records."""
from .ops import CommandError, Op, parse_ops
from .position import key_between, keys_between
from .service import (
    affected_apps, apply, confirm, create_change_set, dismiss, expand_stitches, find_duplicate, load_model,
    preview, rebalance, run, run_gesture, undo, update_ops,
)

__all__ = [
    'CommandError', 'Op', 'parse_ops', 'key_between', 'keys_between', 'affected_apps', 'apply', 'confirm',
    'create_change_set', 'dismiss', 'expand_stitches', 'find_duplicate', 'load_model', 'preview', 'rebalance',
    'run', 'run_gesture', 'undo', 'update_ops',
]
