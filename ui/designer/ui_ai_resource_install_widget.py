# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_ai_resource_install_widget.ui'
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

class Ui_AiResourceInstallWidget(object):
    def setupUi(self, AiResourceInstallWidget, theme: Type[Theme]):
        if not AiResourceInstallWidget.objectName():
            AiResourceInstallWidget.setObjectName(u"AiResourceInstallWidget")
        AiResourceInstallWidget.resize(622, 334)
        self.main_layout = QVBoxLayout(AiResourceInstallWidget)
        self.main_layout.setSpacing(16)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title = HTitle(AiResourceInstallWidget, theme=theme)
        self.title.setObjectName(u"title")

        self.main_layout.addWidget(self.title)

        self.subtitle = HSubtitle(AiResourceInstallWidget, theme=theme)
        self.subtitle.setObjectName(u"subtitle")
        self.subtitle.setMaximumSize(QSize(16777215, 48))
        self.subtitle.setWordWrap(True)

        self.main_layout.addWidget(self.subtitle)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_4 = HLabel(AiResourceInstallWidget, theme=theme)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.label_3 = HLabel(AiResourceInstallWidget, theme=theme)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.label_5 = HLabel(AiResourceInstallWidget, theme=theme)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)


        self.main_layout.addLayout(self.verticalLayout)

        self.progress_layout = QVBoxLayout()
        self.progress_layout.setObjectName(u"progress_layout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = HLabel(AiResourceInstallWidget, theme=theme)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.label_2 = HLabel(AiResourceInstallWidget, theme=theme)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout.addWidget(self.label_2)


        self.progress_layout.addLayout(self.horizontalLayout)

        self.progress_bar = HProgressBar(AiResourceInstallWidget, theme=theme)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)

        self.progress_layout.addWidget(self.progress_bar)


        self.main_layout.addLayout(self.progress_layout)

        self.verticalSpacer_2 = QSpacerItem(543, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.verticalSpacer_2)

        self.comment = HComment(AiResourceInstallWidget, theme=theme)
        self.comment.setObjectName(u"comment")
        self.comment.setMaximumSize(QSize(16777215, 48))
        self.comment.setWordWrap(True)

        self.main_layout.addWidget(self.comment)


        self.retranslateUi(AiResourceInstallWidget)

        QMetaObject.connectSlotsByName(AiResourceInstallWidget)
    # setupUi

    def retranslateUi(self, AiResourceInstallWidget):
        AiResourceInstallWidget.setWindowTitle(QCoreApplication.translate("AiResourceInstallWidget", u"Form", None))
        self.title.setText(QCoreApplication.translate("AiResourceInstallWidget", u"Installation of AI Computational Resources", None))
        self.subtitle.setText(QCoreApplication.translate("AiResourceInstallWidget", u"Some additional software will be installed adapted to your system:", None))
        self.label_4.setText(QCoreApplication.translate("AiResourceInstallWidget", u"- Nvidia TensorRT", None))
        self.label_3.setText(QCoreApplication.translate("AiResourceInstallWidget", u"- PyTorch (CUDA)", None))
        self.label_5.setText(QCoreApplication.translate("AiResourceInstallWidget", u"- Microsoft DirectML", None))
        self.label.setText(QCoreApplication.translate("AiResourceInstallWidget", u"Installing AI Computational Resources...", None))
        self.label_2.setText(QCoreApplication.translate("AiResourceInstallWidget", u"100%", None))
        self.comment.setText(QCoreApplication.translate("AiResourceInstallWidget", u"You choose to keep the downloaded files. You can remove these files in the settings window.", None))
    # retranslateUi

