Windows embeddable package (64-bit)

python-3.12.10-embed-amd64.zip


🧭 1. Enable normal module importing

Open the file:
python312._pth

Uncomment to run site.main() automatically

🧰 2. Bootstrapping pip

Since the embeddable build doesn’t ship pip, you can add it manually:

Option A — Use ensurepip (preferred if it works)

Try this in PowerShell: .\python.exe -m ensurepip

Option B — Manual pip bootstrap
Download get-pip.py from the official source:
https://bootstrap.pypa.io/get-pip.py
.\python.exe get-pip.py

That will install pip and create a Lib\site-packages and Scripts\ folder inside your embed dir.

You’ll now have:
A:\herlegon\python-win32\python-3.12.10-embed-amd64\
 ├─ python.exe
 ├─ Lib\
 │   └─ site-packages\
 ├─ Scripts\
 │   └─ pip.exe
 └─ ...

🧩 3. Install packages (from PyPI or local)

Once pip works, you can install dependencies:

From PyPI: .\python.exe -m pip install requests
From local wheels: .\python.exe -m pip install --no-index --find-links=A:\deps\ requests

🧩 5. Optional: calling from another program
If another app needs to call your Python code:

Simplest: Call the batch file or python.exe with your script.

Advanced: Embed python312.dll directly via the Python C API (Py_Initialize(), etc.), setting PYTHONHOME to your embed folder.

🧹 6. Distribution tip

Zip up everything under python-3.12.10-embed-amd64 plus your scripts, and you’ll have a completely portable Python runtime.

You can even preinstall dependencies into it by running:
.\python.exe -m pip install -t Lib\site-packages\ <packages>

🧰 2. Minimal isolated environment


```python
import os
import subprocess
from pathlib import Path

embed_dir = Path(r"A:\herlegon\python-win32\python-3.12.10-embed-amd64")
python_exe = embed_dir / "python.exe"

# Build a minimal environment
clean_env = {
    "PYTHONHOME": str(embed_dir),
    "PATH": str(embed_dir),
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
    "WINDIR": os.environ.get("WINDIR", "C:\\Windows"),
}

# Run a test command
result = subprocess.run(
    [str(python_exe), "-c", "import sys; print(sys.prefix); print(sys.path)"],
    env=clean_env,
    capture_output=True,
    text=True,
)
print(result.stdout)
```

🧩 3. (Optional) Harden with extra cleanup

This will neutralize things like:

CONDA_PREFIX
PYTHONPATH
PYTHONUSERBASE
PYTHONNOUSERSITE

```python
clean_env = {
    k: v for k, v in os.environ.items()
    if not k.startswith("PYTHON") and not k.startswith("CONDA")
}
clean_env.update({
    "PYTHONHOME": str(embed_dir),
    "PATH": str(embed_dir),
    "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
})
```

```python
import sys, os
print("Prefix:", sys.prefix)
print("Base prefix:", sys.base_prefix)
print("Exec prefix:", sys.exec_prefix)
print("Python path:", sys.path)
print("User site:", getattr(sys, 'base_user_site', '(none)'))
print("Env filtered:", [k for k in os.environ if 'PYTHON' in k or 'CONDA' in k])
```


🧩 1. What python312.zip is

In short:
python312.zip is a ZIP archive of the Python standard library (Lib/ folder).

It’s a compact, read-only form of all the .py files you’d normally find in: `C:\Python312\Lib\`


📦 2. Why it’s zipped in the embeddable version

The embeddable package is designed for redistribution and embedding, not development.
It aims to be:

- Portable: everything lives in one folder
- Small: no need for hundreds of .py files
- Fast to unpack: single ZIP file, ready to run
- Read-only safe: doesn’t require write access or user-specific installs

The ZIP is automatically added to sys.path at startup.
Python transparently imports modules from inside that archive using the built-in zipimport mechanism.

So from the interpreter’s perspective, it’s just as if those modules were regular .py files in Lib/.

🧩 6. TL;DR

| Item                      | Regular install                | Embeddable                 |
| ------------------------- | ------------------------------ | -------------------------- |
| Standard library location | `Lib/` directory               | `python312.zip` archive    |
| Editable by user          | ✅ yes                          | ❌ read-only by default     |
| Default import path       | filesystem                     | zipimport                  |
| Size                      | Larger                         | Smaller                    |
| Use case                  | Development / full environment | Embedding / redistribution |


🧰 Tricks to minimize startup overhead further
1. Use the -S flag if you don’t need site imports
python.exe -S myscript.py
2. Precompile bytecode in the zip
If you control the build, you can include pre-compiled .pyc files in python312.zip.
This avoids parsing .py files at startup. Example:
```python
python.exe -m compileall -b Lib/
zip -r python312.zip Lib/
```

3. Use PYTHONOPTIMIZE=1
set PYTHONOPTIMIZE=1
python.exe myscript.py

5. Use subprocess.run(..., env=clean_env) as before
Filtering out Conda/system vars avoids unnecessary path resolution.

🚀 TL;DR – The fast, isolated setup
✅ Keep python312.zip zipped (do not extract)
✅ Add only Lib\site-packages for your deps
✅ Trim python312._pth to minimal lines
✅ Optionally use -S or PYTHONOPTIMIZE=1
✅ Use a clean env in subprocess

