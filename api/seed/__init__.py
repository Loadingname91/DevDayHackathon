"""The demo seed: canonical rows (data.py), writing them into a workspace (load.py), and the CLI (__main__.py)."""
from .load import build_blocks, demo_spec, ensure_demo_user, ensure_workspace, reset_workspace

__all__ = ['build_blocks', 'demo_spec', 'ensure_demo_user', 'ensure_workspace', 'reset_workspace']
