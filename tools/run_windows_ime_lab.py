"""Launch a disposable Windows Blender UI for real IME verification."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    if sys.platform != "win32":
        raise SystemExit("Run this launcher on Windows with a local Blender installation.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    executable = args.blender.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="node-console-windows-ime-") as directory:
        env = dict(os.environ, NC_WINDOWS_IME_LAB=directory,
                   BLENDER_USER_CONFIG=str(Path(directory) / "config"),
                   BLENDER_USER_SCRIPTS=str(Path(directory) / "scripts"))
        subprocess.run([str(executable), "--factory-startup", "--disable-autoexec", "--python",
                        str(Path(__file__).with_name("windows_ime_lab.py"))], env=env, check=True)


if __name__ == "__main__":
    main()
