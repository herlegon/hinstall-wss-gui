# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_ffmpeg_selection_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from typing import Type
from hwidgets import (
    HCheckBox,
    HComboBox,
    HDoubleSpinBox,
    HFrame,
    HLabel,
    HLineEdit,
    HOutlinedButton,
    HPlainTextEdit,
    HRadioButton,
    HScrollBar,
    HSlider,
    HSpinBox,
    HAppTitle,
    HButtonGroup,
    HCard,
    HComment,
    HDescription,
    HDivider,
    HFramelessButton,
    HGreyButtonGroup,
    HHorizontalDivider,
    HIndetProgressBar,
    HIndetProgressBarM2,
    HIndetProgressBarR,
    HLogViewer,
    HOutlinedButton,
    HProgressBar,
    HProgressBarM3,
    HRadialProgress,
    HStepIndicator,
    HStrongButton,
    HStrongGreyButton,
    HSubtitle,
    HSwitch,
    HTitle,
    HToggleButton,
    HToggleButton,
    HToggleGreyButton,
    HVerticalDivider,
    Theme,
)

class Ui_FFmpegSelectionWidget(object):
    def setupUi(self, FFmpegSelectionWidget, theme: Type[Theme]):
        if not FFmpegSelectionWidget.objectName():
            FFmpegSelectionWidget.setObjectName(u"FFmpegSelectionWidget")
        FFmpegSelectionWidget.resize(640, 585)
        self.main_layout = QVBoxLayout(FFmpegSelectionWidget)
        self.main_layout.setSpacing(16)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title = HTitle(FFmpegSelectionWidget, theme=theme)
        self.title.setObjectName(u"title")

        self.main_layout.addWidget(self.title)

        self.subtitle = HSubtitle(FFmpegSelectionWidget, theme=theme)
        self.subtitle.setObjectName(u"subtitle")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.subtitle.sizePolicy().hasHeightForWidth())
        self.subtitle.setSizePolicy(sizePolicy)
        self.subtitle.setMinimumSize(QSize(0, 24))
        self.subtitle.setMaximumSize(QSize(16777215, 24))

        self.main_layout.addWidget(self.subtitle)

        self.verticalSpacer_2 = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.verticalSpacer_2)

        self.selection_layout = QVBoxLayout()
        self.selection_layout.setSpacing(20)
        self.selection_layout.setObjectName(u"selection_layout")
        self.minimal_layout = QVBoxLayout()
        self.minimal_layout.setSpacing(3)
        self.minimal_layout.setObjectName(u"minimal_layout")
        self.radio_button_minimal = HRadioButton(FFmpegSelectionWidget, theme=theme)
        self.group_ffmpeg = QButtonGroup(FFmpegSelectionWidget)
        self.group_ffmpeg.setObjectName(u"group_ffmpeg")
        self.group_ffmpeg.addButton(self.radio_button_minimal)
        self.radio_button_minimal.setObjectName(u"radio_button_minimal")
        self.radio_button_minimal.setChecked(True)

        self.minimal_layout.addWidget(self.radio_button_minimal)

        self.comment_minimal = HComment(FFmpegSelectionWidget, theme=theme)
        self.comment_minimal.setObjectName(u"comment_minimal")
        self.comment_minimal.setIndent(40)

        self.minimal_layout.addWidget(self.comment_minimal, 0, Qt.AlignmentFlag.AlignTop)


        self.selection_layout.addLayout(self.minimal_layout)

        self.third_party_layout = QVBoxLayout()
        self.third_party_layout.setSpacing(3)
        self.third_party_layout.setObjectName(u"third_party_layout")
        self.radio_button_third_party = HRadioButton(FFmpegSelectionWidget, theme=theme)
        self.group_ffmpeg.addButton(self.radio_button_third_party)
        self.radio_button_third_party.setObjectName(u"radio_button_third_party")
        self.radio_button_third_party.setChecked(False)

        self.third_party_layout.addWidget(self.radio_button_third_party)

        self.comment_third_party = HComment(FFmpegSelectionWidget, theme=theme)
        self.comment_third_party.setObjectName(u"comment_third_party")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comment_third_party.sizePolicy().hasHeightForWidth())
        self.comment_third_party.setSizePolicy(sizePolicy1)
        self.comment_third_party.setIndent(40)

        self.third_party_layout.addWidget(self.comment_third_party, 0, Qt.AlignmentFlag.AlignTop)


        self.selection_layout.addLayout(self.third_party_layout)

        self.installed_ffmpeg = QVBoxLayout()
        self.installed_ffmpeg.setSpacing(3)
        self.installed_ffmpeg.setObjectName(u"installed_ffmpeg")
        self.radio_button_user = HRadioButton(FFmpegSelectionWidget, theme=theme)
        self.group_ffmpeg.addButton(self.radio_button_user)
        self.radio_button_user.setObjectName(u"radio_button_user")

        self.installed_ffmpeg.addWidget(self.radio_button_user)

        self.comment_external = HComment(FFmpegSelectionWidget, theme=theme)
        self.comment_external.setObjectName(u"comment_external")
        self.comment_external.setIndent(40)

        self.installed_ffmpeg.addWidget(self.comment_external, 0, Qt.AlignmentFlag.AlignTop)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(40, -1, -1, -1)
        self.outlined_button_browse = HOutlinedButton(FFmpegSelectionWidget, theme=theme)
        self.outlined_button_browse.setObjectName(u"outlined_button_browse")
        self.outlined_button_browse.setMaximumSize(QSize(24, 16777215))

        self.horizontalLayout.addWidget(self.outlined_button_browse)

        self.line_edit_ffmpeg_dir = HLineEdit(FFmpegSelectionWidget, theme=theme)
        self.line_edit_ffmpeg_dir.setObjectName(u"line_edit_ffmpeg_dir")
        self.line_edit_ffmpeg_dir.setMinimumSize(QSize(500, 0))
        self.line_edit_ffmpeg_dir.setMaximumSize(QSize(500, 16777215))

        self.horizontalLayout.addWidget(self.line_edit_ffmpeg_dir)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.installed_ffmpeg.addLayout(self.horizontalLayout)


        self.selection_layout.addLayout(self.installed_ffmpeg)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.selection_layout.addItem(self.verticalSpacer)

        self.disclaimer = HLabel(FFmpegSelectionWidget, theme=theme)
        self.disclaimer.setObjectName(u"disclaimer")
        self.disclaimer.setWordWrap(True)

        self.selection_layout.addWidget(self.disclaimer, 0, Qt.AlignmentFlag.AlignTop)


        self.main_layout.addLayout(self.selection_layout)


        self.retranslateUi(FFmpegSelectionWidget)

        QMetaObject.connectSlotsByName(FFmpegSelectionWidget)
    # setupUi

    def retranslateUi(self, FFmpegSelectionWidget):
        FFmpegSelectionWidget.setWindowTitle(QCoreApplication.translate("FFmpegSelectionWidget", u"Form", None))
        self.title.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"FFmpeg notice & selection", None))
        self.subtitle.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Select which FFmpeg build to use for media processing.", None))
        self.radio_button_minimal.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Minimal FFmpeg", None))
        self.comment_minimal.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Free codecs included: AV1, VP8, VP9, DNxHD, Vorbis, Opus, FLAC, PCM.\n"
"H.264/H.265 decoding included for playback support.\n"
"Hardware-accelerated H.264/H.265 encoders (requires an NVIDIA GPU).\n"
"\u26a0\ufe0fDoes NOT include software H.264/H.265, AAC, or MP3 encoders.\n"
"Safe for commercial use without additional licenses.", None))
        self.radio_button_third_party.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Download FFmpeg from a third-party", None))
        self.comment_third_party.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Includes full software H.264/H.265/AAC/MP3 encoders (GPL and patent-encumbered).\n"
"Provided by a third party. You are responsible for any licenses or patents.\n"
"Commercial use may require separate patent licenses.", None))
        self.radio_button_user.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Use an existing FFmpeg on your system", None))
        self.comment_external.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Select a pre-installed FFmpeg binary.\n"
"You are responsible for license and patent compliance, including commercial use.", None))
        self.outlined_button_browse.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"...", None))
        self.line_edit_ffmpeg_dir.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"No file selected", None))
        self.disclaimer.setText(QCoreApplication.translate("FFmpegSelectionWidget", u"Disclaimer: neither Herlegon nor their developers are responsible for the choice of FFmpeg binary. By selecting an external or third-party FFmpeg, you acknowledge that you are responsible for complying with all applicable licenses and patent obligations, including any requirements for commercial use.", None))
    # retranslateUi

