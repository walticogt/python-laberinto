from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_PRESETS: dict[str, int] = {
    "simple": 15,
    "medium": 25,
    "complex": 40,
}

DISPLAY_LABELS: dict[str, str] = {
    "simple": "Básico",
    "medium": "Medio",
    "complex": "Complejo",
}

PRESET_KEYS: tuple[str, ...] = ("simple", "medium", "complex")

DEFAULT_CONFIG_PATH: Path = Path.home() / ".laberinto.json"

LARGE_N_WARN_THRESHOLD = 60


def _validate_preset_value(key: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"preset '{key}' must be an integer, got {type(value).__name__}: {value!r}"
        )
    if value < 2:
        raise ValueError(f"preset '{key}' must be >= 2, got {value}")
    return value


def load_presets(path: Path | None = None) -> dict[str, int]:
    config_path = path or DEFAULT_CONFIG_PATH
    presets = dict(DEFAULT_PRESETS)

    if not config_path.exists():
        return presets

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(
            f"warning: no se pudo leer {config_path} ({exc}); usando valores por defecto.",
            file=sys.stderr,
        )
        return presets

    file_presets = raw.get("presets") if isinstance(raw, dict) else None
    if not isinstance(file_presets, dict):
        return presets

    for key in PRESET_KEYS:
        if key in file_presets:
            value = file_presets[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                print(
                    f"warning: preset '{key}' inválido en {config_path} ({value!r}); "
                    f"usando default {DEFAULT_PRESETS[key]}.",
                    file=sys.stderr,
                )
                continue
            presets[key] = value

    return presets


def save_presets(presets: dict[str, int], path: Path | None = None) -> None:
    validated: dict[str, int] = {}
    for key in PRESET_KEYS:
        if key not in presets:
            raise ValueError(f"preset '{key}' faltante")
        validated[key] = _validate_preset_value(key, presets[key])

    for key, value in validated.items():
        if value > LARGE_N_WARN_THRESHOLD:
            print(
                f"warning: preset '{key}' N={value} puede producir líneas demasiado "
                f"finas para imprimir.",
                file=sys.stderr,
            )

    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")
    payload = json.dumps({"presets": validated}, indent=2, ensure_ascii=False) + "\n"
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, config_path)


def resolve(presets: dict[str, int], name: str) -> int:
    if name not in presets:
        allowed = ", ".join(PRESET_KEYS)
        raise ValueError(f"dificultad desconocida: {name!r}. Opciones: {allowed}")
    return presets[name]
