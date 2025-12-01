# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_backend_install_widget.ui'
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

class Ui_BackendWidget(object):
    def setupUi(self, BackendWidget, theme: Type[Theme]):
        if not BackendWidget.objectName():
            BackendWidget.setObjectName(u"BackendWidget")
        BackendWidget.resize(987, 231)
        self.main_layout = QVBoxLayout(BackendWidget)
        self.main_layout.setSpacing(16)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title = HTitle(BackendWidget, theme=theme)
        self.title.setObjectName(u"title")

        self.main_layout.addWidget(self.title)

        self.subtitle = HSubtitle(BackendWidget, theme=theme)
        self.subtitle.setObjectName(u"subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.subtitle.setWordWrap(True)

        self.main_layout.addWidget(self.subtitle)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = HLabel(BackendWidget, theme=theme)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_2 = HLabel(BackendWidget, theme=theme)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.progress_bar = HProgressBar(BackendWidget, theme=theme)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(24)

        self.verticalLayout_2.addWidget(self.progress_bar)


        self.main_layout.addLayout(self.verticalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.verticalSpacer_2)


        self.retranslateUi(BackendWidget)

        QMetaObject.connectSlotsByName(BackendWidget)
    # setupUi

    def retranslateUi(self, BackendWidget):
        BackendWidget.setWindowTitle(QCoreApplication.translate("BackendWidget", u"Form", None))
        self.title.setText(QCoreApplication.translate("BackendWidget", u"Installation of the processing server", None))
        self.subtitle.setText(QCoreApplication.translate("BackendWidget", u"This software is a framework in charge of converting models, processing images, video. It uses the Computational Resources available on your system.", None))
        self.label.setText(QCoreApplication.translate("BackendWidget", u"Downloading", None))
        self.label_2.setText(QCoreApplication.translate("BackendWidget", u"100%", None))
    # retranslateUi

