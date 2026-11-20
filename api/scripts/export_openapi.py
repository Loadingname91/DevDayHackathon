"""Write api/openapi.json from the contract router (spec/split.md §2).

Run from the repo root: uv run --project api python -m api.scripts.export_openapi
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

from api.contract import router

OUT = Path(__file__).resolve().parents[1] / 'openapi.json'


def build() -> dict:
    app = FastAPI(title='Quilt API', version='0.1.0', separate_input_output_schemas=False)
    app.include_router(router, prefix='/api')
    return app.openapi()


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
