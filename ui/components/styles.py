
from dataclasses import dataclass
from typing import NamedTuple
from hwidgets import HStyle


@dataclass(slots=True)
class FontConfig(NamedTuple):
    family: str = "Segoe UI"
    size: int = 10
    weight: int = 400  # 400=normal, 700=bold


@dataclass(slots=True)
class InstallStyle(HStyle):
    window_bgd: str = "#252528"

    # Combobox
    widget_bgd: str = "#4F4D53"
    text_color: str = "#d4d4d8"
    # selection_bgd: str = "#454546"
    hover_bgd: str = "#66636D"

    # normal_button: str = "#5545bd"
    # hover_button: str = "#6a5bcc"
    # pressed_button: str = "#4539a0"
    # disabled_button: str = "#8b88c7"

    normal_button: str = "#5442bd"
    hover_button: str = "#7777FF"
    pressed_button: str = "#5555B3"
    disabled_button: str = "#A3A3D1"

    # hover_bgd: str ="#77f"
    selection_bgd: str = "#5545bd"

    selected_text: str = "#5545bd"


    border: str = "#505053" # same as hover

    checked: str = "#5442bd"

    selected: str = "#5442bd"


    # checkbox
    enabled = "#4B8DD8"
    disabled_bgd = "#313131"

    disabled_text = "#4E4E4E"
    checked_text = "#4632c7"

    divider: str = "#3B3B3B" # same as hover

    pressed: str = "#66636D" # same as hover

    title_text: str = "#5442bd"


    # Accent (hover)	"#4e83c2"	 # Slightly lighter for hover feedback
    # Accent (pressed)	"#345d8a"	# Darker variant for pressed/active states
    # Accent (disabled)	"#2e3c4f"	# Desaturated accent for disabled controls
    # Base background	"#1e1f22"	# Main window / panel background
    # Widget background	"#2a2c30"	# Lighter inner surfaces (e.g. combobox, buttons)
    # Hover background	"#34373d"	# Light hover elevation
    # Text (normal)	"#e6e6e6"	# Soft white for text, not full white
    # Text (disabled)	"#777"	# Dimmed gray
    # Border (neutral)	"#3a3d42"	# Subtle border for structure
    # Border (focus)	"#3d6ea8"	# Accent border when focused


# Checked / Active	#422ca1	Checkbox, radio, selected item
# Hover / Focused	#5948c4	Slightly brighter — gives visual lift
# Pressed	#352283	Darker tone for click feedback
# Disabled	#2d2b3e	Muted, low-contrast desaturation
