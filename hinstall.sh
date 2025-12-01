#!/usr/bin/env bash
set -e  # exit immediately on error

SKIP_UI=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-ui)
            SKIP_UI=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# === UI generation section ===
if [ "$SKIP_UI" = false ]; then
    pyside6-uic ./ui/designer/ui_welcome_widget.ui -o ./ui/designer/ui_welcome_widget.py
    # python ./ui/patch_ui.py ./ui/designer/ui_welcome_widget.py
    python ../hwidgets/scripts/q_to_h.py ./ui/designer/ui_welcome_widget.py

    pyside6-uic ./ui/designer/ui_ffmpeg_selection_widget.ui -o ./ui/designer/ui_ffmpeg_selection_widget.py
    python ../hwidgets/scripts/q_to_h.py ./ui/designer/ui_ffmpeg_selection_widget.py

    pyside6-uic ./ui/designer/ui_third_party_install_widget.ui -o ./ui/designer/ui_third_party_install_widget.py
    python ../hwidgets/scripts/q_to_h.py ./ui/designer/ui_third_party_install_widget.py

    pyside6-uic ./ui/designer/ui_backend_install_widget.ui -o ./ui/designer/ui_backend_install_widget.py
    python ../hwidgets/scripts/q_to_h.py ./ui/designer/ui_backend_install_widget.py

    pyside6-uic ./ui/designer/ui_ai_resource_install_widget.ui -o ./ui/designer/ui_ai_resource_install_widget.py
    python ../hwidgets/scripts/q_to_h.py ./ui/designer/ui_ai_resource_install_widget.py

else
    echo "Skipping UI generation (--skip-ui flag detected)"

fi

export QT_QPA_PLATFORM=xcb
python -m ui.hinstall
