#!/usr/bin/env bash
set -euo pipefail

PY_VERSION="3.12.12"

ARCHIVE_PATH="cpython-${PY_VERSION}+20251031-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"

WORKDIR="python-${PY_VERSION}-linux-x86_64-work"
FINAL_TAR="python-${PY_VERSION}-linux-x86_64.tar.gz"
REQ_PKGS=("requests")

# === Build ====================================================================
echo "[*] Cleaning old workdir..."
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

if [ ! -f "$ARCHIVE_PATH" ]; then
    echo "!!! ERROR: Archive not found at $ARCHIVE_PATH"
    exit 1
fi

echo "[*] Using local standalone Python archive:"
echo "    $ARCHIVE_PATH"

echo "[*] Extracting embedded Python..."
tar -xzf "$ARCHIVE_PATH" -C "$WORKDIR" --strip-components=1

cd "$WORKDIR"
PYTHON_BIN="./bin/python3.12"

echo "[*] Bootstrapping pip (ensurepip)..."
$PYTHON_BIN -m ensurepip --upgrade

echo "[*] Upgrading packaging tools..."
$PYTHON_BIN -m pip install --no-cache-dir --upgrade pip setuptools wheel

echo "[*] Installing requested packages: ${REQ_PKGS[*]}"
$PYTHON_BIN -m pip install --no-cache-dir "${REQ_PKGS[@]}"

echo "[*] Precompiling stdlib and site-packages..."
$PYTHON_BIN -m compileall -q -f lib/python3.12 || true
$PYTHON_BIN -m compileall -q -f lib64/python3.12 || true
SITEPKG_DIR=$($PYTHON_BIN -c "import site; print(site.getsitepackages()[0])")
$PYTHON_BIN -m compileall -q -f "$SITEPKG_DIR" || true

echo "[*] Cleaning unnecessary files..."
rm -rf ./lib/python3.12/test ./lib/python3.12/ensurepip ./lib/python3.12/idlelib ./lib/python3.12/tkinter || true
find . -type d -name "__pycache__" -empty -delete

cd ..
echo "[*] Creating final tarball: $FINAL_TAR"
tar -czf "$FINAL_TAR" -C "$WORKDIR" .

echo "[✓] Build complete: $FINAL_TAR"
