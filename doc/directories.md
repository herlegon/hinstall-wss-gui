herlegon/
    ├── cache/
    ├── python/
    │   ├── bootstrap.py            ← entry point
    │   ├── modules/
    │       ├── hwss/
    │       │   ├── __init__.py
    │       │   ├── ...
    │       │   └── wss.py          ← websocket server for install
    │       │
    │       ├── hinstall/
    │       │   ├── __init__.py
    │       │   └── ...
    │       │
    │       └── hsys/               ← version x.y.z
    │           ├── __init__.py
    │           └── ...
    │
    │
    ├── pynnlib/
    │   ├── __init__.py
    │   └── ...
    │
    ├── hconvert/
    │   ├── __init__.py
~~  │   ├── hconvert.toml       ← package's version~~
    │   ├── wss.py              ← bootstrap jump to this if arg==hvideo
    │   └── hsys/               ← version xx.yy.zz
    │       ├── __init__.py
    │       └── ...
    │
    ├── hvideo/
    │   ├── __init__.py
~~  │   ├── hvideo.toml         ← package's version~~
    │   ├── wss.py              ← bootstrap jump to this if arg==hvideo
    │   └── hsys/               ← version xxx.yyy.zzz
    │       ├── __init__.py
    │       └── ...
    │














