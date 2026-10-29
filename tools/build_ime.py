"""Build the signed universal macOS receiver and its offline resource envelope."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = next(ast.literal_eval(node.value) for node in ast.parse((ROOT / "__init__.py").read_text()).body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ADDON_VERSION" for t in node.targets))
    source = ROOT / "ime_input/ime_cocoa.m"
    suffix = version.replace(".", "_")
    with tempfile.TemporaryDirectory(prefix="nc-native-build-") as directory:
        output = Path(directory) / ("nc_ime_" + suffix + ".dylib")
        subprocess.run(["xcrun", "clang", "-dynamiclib", "-fobjc-arc", "-framework", "Cocoa",
                        "-arch", "arm64", "-arch", "x86_64", "-mmacosx-version-min=11.0",
                        "-Wall", "-Wextra", "-Werror", "-DNCIMEClient=NCIMEClient_" + suffix,
                        "-Wl,-install_name,@loader_path/" + output.name,
                        str(source), "-o", str(output)], check=True)
        subprocess.run(["codesign", "--force", "--sign", "-", str(output)], check=True)
        subprocess.run(["codesign", "--verify", "--strict", str(output)], check=True)
        architectures = subprocess.check_output(["lipo", "-archs", str(output)], text=True).split()
        assert set(architectures) == {"arm64", "x86_64"}
        data = output.read_bytes()
        payload = {"format": 1, "version": version, "architectures": architectures,
                   "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                   "sha256": hashlib.sha256(data).hexdigest(),
                   "data": base64.b64encode(data).decode("ascii")}
        (ROOT / "ime_input/macos.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("IME_RESOURCE_OK", version, architectures, payload["sha256"])


if __name__ == "__main__":
    main()
