# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_welcome_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

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

class Ui_WelcomeWidget(object):
    def setupUi(self, WelcomeWidget, theme: Type[Theme]):
        if not WelcomeWidget.objectName():
            WelcomeWidget.setObjectName(u"WelcomeWidget")
        WelcomeWidget.resize(695, 373)
        self.main_layout = QVBoxLayout(WelcomeWidget)
        self.main_layout.setSpacing(16)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.title = HTitle(WelcomeWidget, theme=theme)
        self.title.setObjectName(u"title")

        self.main_layout.addWidget(self.title)

        self.subtitle = HSubtitle(WelcomeWidget, theme=theme)
        self.subtitle.setObjectName(u"subtitle")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.subtitle.sizePolicy().hasHeightForWidth())
        self.subtitle.setSizePolicy(sizePolicy)
        self.subtitle.setMinimumSize(QSize(0, 24))
        self.subtitle.setMaximumSize(QSize(16777215, 24))

        self.main_layout.addWidget(self.subtitle)

        self.verticalSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.main_layout.addItem(self.verticalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.checkbox_cache = HCheckBox(WelcomeWidget, theme=theme)
        self.checkbox_cache.setObjectName(u"checkbox_cache")

        self.verticalLayout_3.addWidget(self.checkbox_cache)

        self.comment = HComment(WelcomeWidget, theme=theme)
        self.comment.setObjectName(u"comment")
        self.comment.setScaledContents(False)
        self.comment.setMargin(0)
        self.comment.setIndent(40)

        self.verticalLayout_3.addWidget(self.comment, 0, Qt.AlignmentFlag.AlignTop)


        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.custom_install_dir_layout = QVBoxLayout()
        self.custom_install_dir_layout.setSpacing(3)
        self.custom_install_dir_layout.setObjectName(u"custom_install_dir_layout")
        self.checkbox_custom_dir = HCheckBox(WelcomeWidget, theme=theme)
        self.checkbox_custom_dir.setObjectName(u"checkbox_custom_dir")
        self.checkbox_custom_dir.setEnabled(False)

        self.custom_install_dir_layout.addWidget(self.checkbox_custom_dir)

        self.custom_dir_layout = QHBoxLayout()
        self.custom_dir_layout.setObjectName(u"custom_dir_layout")
        self.custom_dir_layout.setContentsMargins(40, -1, -1, -1)
        self.lineedit_custom_dir = HLineEdit(WelcomeWidget, theme=theme)
        self.lineedit_custom_dir.setObjectName(u"lineedit_custom_dir")
        self.lineedit_custom_dir.setEnabled(False)
        self.lineedit_custom_dir.setMinimumSize(QSize(300, 0))
        self.lineedit_custom_dir.setMaximumSize(QSize(500, 16777215))

        self.custom_dir_layout.addWidget(self.lineedit_custom_dir, 0, Qt.AlignmentFlag.AlignLeft)

        self.icon_button_browse = HToggleButton(WelcomeWidget, theme=theme)
        self.icon_button_browse.setObjectName(u"icon_button_browse")
        self.icon_button_browse.setEnabled(False)
        self.icon_button_browse.setMaximumSize(QSize(24, 16777215))

        self.custom_dir_layout.addWidget(self.icon_button_browse)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.custom_dir_layout.addItem(self.horizontalSpacer)


        self.custom_install_dir_layout.addLayout(self.custom_dir_layout)


        self.verticalLayout.addLayout(self.custom_install_dir_layout)

        self.checkbox_use_as_global = HCheckBox(WelcomeWidget, theme=theme)
        self.checkbox_use_as_global.setObjectName(u"checkbox_use_as_global")
        self.checkbox_use_as_global.setChecked(True)

        self.verticalLayout.addWidget(self.checkbox_use_as_global)


        self.main_layout.addLayout(self.verticalLayout)

        self.verticalSpacer_bottom = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.verticalSpacer_bottom)

        self.comment_required_disk_space = HComment(WelcomeWidget, theme=theme)
        self.comment_required_disk_space.setObjectName(u"comment_required_disk_space")

        self.main_layout.addWidget(self.comment_required_disk_space)


        self.retranslateUi(WelcomeWidget)

        QMetaObject.connectSlotsByName(WelcomeWidget)
    # setupUi

    def retranslateUi(self, WelcomeWidget):
        WelcomeWidget.setWindowTitle(QCoreApplication.translate("WelcomeWidget", u"Form", None))
        self.title.setText(QCoreApplication.translate("WelcomeWidget", u"Welcome", None))
        self.subtitle.setText(QCoreApplication.translate("WelcomeWidget", u"This will install third parties software and computational resources based on your system.", None))
        self.checkbox_cache.setText(QCoreApplication.translate("WelcomeWidget", u"Cache downloaded packages", None))
        self.comment.setText(QCoreApplication.translate("WelcomeWidget", u"Used when reinstalling or updating the software to save bandwidth.\n"
"This will use approximately between 1 and 4GB of disk space depending on your system but allows\n"
"faster reinstallation without re-downloading big packages.", None))
        self.checkbox_custom_dir.setText(QCoreApplication.translate("WelcomeWidget", u"Custom installation directory (Not available yet)", None))
        self.icon_button_browse.setText(QCoreApplication.translate("WelcomeWidget", u"...", None))
        self.checkbox_use_as_global.setText(QCoreApplication.translate("WelcomeWidget", u"Use the installation settings as the default for all products (save disk space, recommended)", None))
        self.comment_required_disk_space.setText(QCoreApplication.translate("WelcomeWidget", u"Required space: 7GB", None))
    # retranslateUi

