from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_file(path: Path) -> bool:
    target = str(Path(path).resolve())
    try:
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", target])
        else:
            print(
                f"warning: plataforma {sys.platform!r} no soportada para auto-abrir; "
                f"abre manualmente: {target}",
                file=sys.stderr,
            )
            return False
        return True
    except Exception as exc:
        print(
            f"warning: no se pudo abrir {target}: {exc}",
            file=sys.stderr,
        )
        return False
