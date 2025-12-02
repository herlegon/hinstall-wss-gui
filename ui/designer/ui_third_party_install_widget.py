# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_third_party_install_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QProgressBar,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

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

class Ui_ThirdPartiesInstall(object):
    def setupUi(self, ThirdPartiesInstall, theme: Type[Theme]):
        if not ThirdPartiesInstall.objectName():
            ThirdPartiesInstall.setObjectName(u"ThirdPartiesInstall")
        ThirdPartiesInstall.resize(528, 219)
        self.main_layout = QVBoxLayout(ThirdPartiesInstall)
        self.main_layout.setSpacing(16)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title = HTitle(ThirdPartiesInstall, theme=theme)
        self.title.setObjectName(u"title")

        self.main_layout.addWidget(self.title)

        self.subtitle = HSubtitle(ThirdPartiesInstall, theme=theme)
        self.subtitle.setObjectName(u"subtitle")

        self.main_layout.addWidget(self.subtitle)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(16, -1, -1, -1)
        self.verticalSpacer_2 = QSpacerItem(511, 37, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = HLabel(ThirdPartiesInstall, theme=theme)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_2 = HLabel(ThirdPartiesInstall, theme=theme)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.progress_bar = HProgressBar(ThirdPartiesInstall, theme=theme)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(24)

        self.verticalLayout_2.addWidget(self.progress_bar)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.main_layout.addLayout(self.verticalLayout_2)


        self.retranslateUi(ThirdPartiesInstall)

        QMetaObject.connectSlotsByName(ThirdPartiesInstall)
    # setupUi

    def retranslateUi(self, ThirdPartiesInstall):
        ThirdPartiesInstall.setWindowTitle(QCoreApplication.translate("ThirdPartiesInstall", u"Form", None))
        self.title.setText(QCoreApplication.translate("ThirdPartiesInstall", u"Third-party software", None))
        self.subtitle.setText(QCoreApplication.translate("ThirdPartiesInstall", u"Download and installation of third parties software", None))
        self.label.setText(QCoreApplication.translate("ThirdPartiesInstall", u"Downloading FFmpeg", None))
        self.label_2.setText(QCoreApplication.translate("ThirdPartiesInstall", u"100%", None))
    # retranslateUi

