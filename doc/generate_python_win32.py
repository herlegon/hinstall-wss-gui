import os
import sys
import shutil
import zipfile
import subprocess
import compileall
import urllib.request
from pathlib import Path

# === CONFIGURATION ===
PYTHON_EMBED_ZIP = Path("python-3.12.10-embed-amd64.zip")
OUTPUT_ZIP = Path("python-3.12.10-amd64.zip")
PIP_PACKAGES = ["requests", ]  # Add more if needed
REMOVE_UNUSED = True  # Remove LICENSE, .cat, .txt, etc.


# === PREPARE TEMP DIRECTORY ===
WORKDIR = Path("python-3.12.10-embed-amd64-work")
# workdir = Path(tempfile.mkdtemp(prefix="python_embed_build_"))
# === CLEAN & PREPARE ===
if WORKDIR.exists():
    print(f"[*] Removing existing workdir: {WORKDIR}")
    shutil.rmtree(WORKDIR)
WORKDIR.mkdir(parents=True)
print(f"[*] Using workdir: {WORKDIR.resolve()}")


# === 1. EXTRACT EMBEDDED PYTHON ===
print("[*] Extracting embedded Python...")
with zipfile.ZipFile(PYTHON_EMBED_ZIP, "r") as zf:
    zf.extractall(WORKDIR)


# === 2. ENABLE import site ===
pth_files = list(WORKDIR.glob("*.pth")) + list(WORKDIR.glob("*._pth"))
if not pth_files:
    raise RuntimeError("No _pth file found.")
pth_file = pth_files[0]
print(f"[*] Found path config: {pth_file.name}")
text = pth_file.read_text(encoding="utf-8")
if "import site" not in text:
    text += ("\n" if not text.endswith("\n") else "") + "import site\n"
    pth_file.write_text(text, encoding="utf-8")
    print("    -> Added 'import site' to path file.")
else:
    print("    -> 'import site' already present.")



# === 3. PREPARE minimal Lib structure ===
lib_dir = WORKDIR / "Lib"
lib_dir.mkdir(exist_ok=True)
(lib_dir / "site-packages").mkdir(parents=True, exist_ok=True)



# === 4. DOWNLOAD get-pip.py ===
get_pip = WORKDIR / "get-pip.py"
if not get_pip.exists():
    print("[*] Downloading get-pip.py...")
    urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", get_pip)
else:
    print("[*] Using existing get-pip.py")



# === 5. BOOTSTRAP pip with proper env ===
print("[*] Installing pip into embedded runtime...")
env = os.environ.copy()
env["PYTHONPATH"] = str(WORKDIR / "python312.zip") + os.pathsep + str(lib_dir)

result = subprocess.run(
    [str(WORKDIR / "python.exe"), str(get_pip.resolve()), "--no-warn-script-location"],
    cwd=WORKDIR,
    env=env,
)
if result.returncode != 0:
    print("!!! pip bootstrap failed.")
    sys.exit(result.returncode)


# === 6. ENSURE site-packages visible ===
print("[*] Ensuring site-packages path in ._pth file...")
pth_file = next(WORKDIR.glob("python312._pth"))
lines = [ln.strip() for ln in pth_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
if "Lib" not in lines:
    lines.insert(0, "Lib")
if "Lib\\site-packages" not in lines and "Lib/site-packages" not in lines:
    lines.insert(1, "Lib\\site-packages")
if "import site" not in lines:
    lines.append("import site")
pth_file.write_text("\n".join(lines) + "\n", encoding="utf-8")




# === 6. VERIFY pip ===
print("[*] Checking pip version...")
subprocess.run([str(WORKDIR / "python.exe"), "-m", "pip", "--version"], cwd=WORKDIR)



# === 7. INSTALL PACKAGES ===
print(f"[*] Installing packages: {PIP_PACKAGES}")
subprocess.run(
    [str(WORKDIR / "python.exe"), "-m", "pip", "install", "--no-cache-dir", *PIP_PACKAGES],
    cwd=WORKDIR,
    check=True,
)



# === 8. PRECOMPILE ===
print("[*] Precompiling all .py files to .pyc...")
compileall.compile_dir(lib_dir, force=True, quiet=1)

zip_stdlib = WORKDIR / "python312.zip"
if zip_stdlib.exists():
    print("[*] Extracting and precompiling stdlib...")
    stdlib_extract = WORKDIR / "_stdlib"
    with zipfile.ZipFile(zip_stdlib, "r") as zf:
        zf.extractall(stdlib_extract)
    compileall.compile_dir(stdlib_extract, force=True, quiet=1)
    print("    -> Repacking python312.zip with .pyc only...")
    with zipfile.ZipFile(zip_stdlib, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for pyc in stdlib_extract.rglob("*.pyc"):
            zf.write(pyc, pyc.relative_to(stdlib_extract))
    shutil.rmtree(stdlib_extract)



# === 9. OPTIONAL CLEANUP ===
if REMOVE_UNUSED:
    print("[*] Cleaning unnecessary files...")
    for pattern in (
        # "*.txt",  <- no because licenses
        "*.cat",
        "get-pip.py"
    ):
        for f in WORKDIR.glob(pattern):
            f.unlink(missing_ok=True)



# === 10. PACKAGE FINAL ZIP ===
print("[*] Creating final ZIP...")
if OUTPUT_ZIP.exists():
    OUTPUT_ZIP.unlink()
with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in WORKDIR.rglob("*"):
        zf.write(path, path.relative_to(WORKDIR))

print(f"[✓] Build complete: {OUTPUT_ZIP.resolve()}")