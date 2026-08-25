#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    venv_python = Path(__file__).resolve().parent / "venv" / "Scripts" / "python.exe"
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        os.execv(str(venv_python), [str(venv_python), *sys.argv])

    project_dir = Path(__file__).resolve().parent / "swachhai"
    sys.path.insert(0, str(project_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swachhai.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
