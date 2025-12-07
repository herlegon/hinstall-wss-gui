@echo off
setlocal enabledelayedexpansion

:: Parse command-line arguments
if "%~1"=="--skip-ui" (
    echo Skip UI flag detected, skipping UI generation...

) else (
    echo Running UI generation...

    pyside6-uic .\ui\designer\ui_welcome_widget.ui -o .\ui\designer\ui_welcome_widget.py
    :: python .\ui\patch_ui.py .\ui\designer\ui_welcome_widget.py
    python ..\hwidgets\scripts\q_to_h.py .\ui\designer\ui_welcome_widget.py

    pyside6-uic .\ui\designer\ui_ffmpeg_selection_widget.ui -o .\ui\designer\ui_ffmpeg_selection_widget.py
    python ..\hwidgets\scripts\q_to_h.py .\ui\designer\ui_ffmpeg_selection_widget.py

    pyside6-uic .\ui\designer\ui_third_party_install_widget.ui -o .\ui\designer\ui_third_party_install_widget.py
    python ..\hwidgets\scripts\q_to_h.py .\ui\designer\ui_third_party_install_widget.py

    pyside6-uic .\ui\designer\ui_backend_install_widget.ui -o .\ui\designer\ui_backend_install_widget.py
    python ..\hwidgets\scripts\q_to_h.py .\ui\designer\ui_backend_install_widget.py

    pyside6-uic .\ui\designer\ui_ai_resource_install_widget.ui -o .\ui\designer\ui_ai_resource_install_widget.py
    python ..\hwidgets\scripts\q_to_h.py .\ui\designer\ui_ai_resource_install_widget.py
)

python -m ui.hinstall
