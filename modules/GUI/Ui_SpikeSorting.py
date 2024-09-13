# -*- coding: utf-8 -*-
"""
SpikeAnalysis tool. A tool to analyse neuronal spike activity.

Copyright (C) 2024 Luk Sullock Enzlin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt5.QtCore import (QCoreApplication, QSize, QMetaObject,
                          QRect, Qt, QEvent, QLocale)
from PyQt5.QtGui import (QStandardItem, QBrush, QColor)
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QMenu,
                        QLabel, QLineEdit, QMenuBar, QPushButton, QAction,
                        QSizePolicy, QSpacerItem, QSpinBox, QTabWidget,
                        QWidget, QApplication,QMainWindow, QDoubleSpinBox,
                        QScrollArea, QFrame)

class CheckableComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closeOnLineEditClick=False
        self.firstitem=QStandardItem("Select channel(s)")
        self.firstitem.setBackground(QBrush(QColor(200, 200, 200)))
        self.firstitem.setSelectable(False)
        self.lineEdit().installEventFilter(self)
        self.view().viewport().installEventFilter(self)
        self.model().appendRow(self.firstitem)
        self.model().dataChanged.connect(self.updateLineEditField)
    
    def eventFilter(self, widget, event):
        if widget==self.lineEdit():
            if event.type()==QEvent.Type.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.closeOnLineEditClick=False
                    self.hidePopup()
                else:
                    self.closeOnLineEditClick=True
                    self.showPopup()
                return True
            if event.type()==QEvent.Type.Scroll:
                print(2)
                return True
            return super().eventFilter(widget, event)
        if widget==self.view().viewport():
            if event.type()==QEvent.Type.MouseButtonRelease:
                indx=self.view().indexAt(event.pos())
                item=self.model().item(indx.row())
                if item.checkState()==Qt.CheckState.Checked:
                    item.setCheckState(Qt.CheckState.Unchecked)
                elif item.isSelectable()==True:
                    item.setCheckState(Qt.CheckState.Checked)
                return True
            return super().eventFilter(widget, event)
    
    def updateLineEditField(self):
        text_container=[]
        for ii in range(self.model().rowCount()):
            if self.model().item(ii).checkState()==Qt.CheckState.Checked:
                text_container.append(self.model().item(ii).text())
        text_string=', '.join(text_container)
        if not text_string:
            text_string=self.firstitem.text()
        self.lineEdit().setText(text_string)
    
    def addItems(self, items, itemList=None):
        for ii, text in enumerate(items):
            try:
                data=itemList[ii]
            except (TypeError,IndexError):
                data=None
            self.addItem(text, data)
        
    def addItem(self, text, userData=None):
        item=QStandardItem()
        item.setText(text)
        if userData:
            item.setData(userData)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        item.setSelectable(True)
        self.model().appendRow(item)
        self.updateLineEditField()

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1000, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
#Actions
        self.actionOpen_file = QAction(MainWindow)
        self.actionOpen_file.setObjectName(u"actionOpen_file")
#Buttons
        self.bt_closeplots = QPushButton(self.centralwidget)
        self.bt_closeplots.setObjectName(u"bt_closeplots")
        self.bt_file = QPushButton(self.centralwidget)
        self.bt_file.setObjectName(u"bt_file")
        self.bt_go = QPushButton(self.centralwidget)
        self.bt_go.setObjectName(u"bt_go")
        self.bt_quit = QPushButton(self.centralwidget)
        self.bt_quit.setObjectName(u"bt_quit")
        self.bt_saveall = QPushButton(self.centralwidget)
        self.bt_saveall.setObjectName(u"bt_saveall")
#Checkable comboboxes
        self.ccb_channels = CheckableComboBox()
        self.ccb_channels.setObjectName(u"ccb_channels")
#Checkboxes
        self.cb_amplitudedistribution = QCheckBox(self.centralwidget)
        self.cb_amplitudedistribution.setObjectName(u"cb_amplitudedistribution")
        self.cb_averagewaveform = QCheckBox(self.centralwidget)
        self.cb_averagewaveform.setObjectName(u"cb_averagewaveform")
        self.cb_cutoff = QCheckBox(self.centralwidget)
        self.cb_cutoff.setObjectName(u"cb_cutoff")
        self.cb_externalplot = QCheckBox(self.centralwidget)
        self.cb_externalplot.setObjectName(u"cb_externalplot")
        self.cb_interspikeinterval = QCheckBox(self.centralwidget)
        self.cb_interspikeinterval.setObjectName(u"cb_interspikeinterval")
        self.cb_selectall = QCheckBox(self.centralwidget)
        self.cb_selectall.setObjectName(u"cb_selectall")
        self.cb_selectedframes = QCheckBox(self.centralwidget)
        self.cb_selectedframes.setObjectName(u"cb_selectedframes")
        self.cb_spikesorting = QCheckBox(self.centralwidget)
        self.cb_spikesorting.setObjectName(u"cb_spikesorting")
        self.cb_wholerecording = QCheckBox(self.centralwidget)
        self.cb_wholerecording.setObjectName(u"cb_wholerecording")
#Comboboxes
        self.comb_file = QComboBox(self.centralwidget)
        self.comb_file.setObjectName(u"comb_file")
        self.comb_file.addItem("Select file")
#Labels
        self.lbl_condition = QLabel(self.centralwidget)
        self.lbl_condition.setObjectName(u"lbl_condition")
        self.lbl_file = QLabel(self.centralwidget)
        self.lbl_file.setObjectName(u"lbl_file")
        self.lbl_output = QLabel(self.centralwidget)
        self.lbl_output.setObjectName(u"lbl_output")
        self.lbl_refractair = QLabel(self.centralwidget)
        self.lbl_refractair.setObjectName(u"lbl_refractair")
        self.lbl_thresholds = QLabel(self.centralwidget)
        self.lbl_thresholds.setObjectName(u"lbl_thresholds")
        self.lbl_timeinterval = QLabel(self.centralwidget)
        self.lbl_timeinterval.setObjectName(u"lbl_timeinterval")
        self.lbl_markers = QLabel(self.centralwidget)
        self.lbl_markers.setObjectName(u"lbl_markers")
#Line edits
        self.le_condition = QLineEdit(self.centralwidget)
        self.le_condition.setObjectName(u"le_condition")
        self.le_outputname = QLineEdit(self.centralwidget)
        self.le_outputname.setObjectName(u"le_outputname")
        self.le_thresholds = QLineEdit(self.centralwidget)
        self.le_thresholds.setObjectName(u"le_thresholds")
        self.le_timeinterval = QLineEdit(self.centralwidget)
        self.le_timeinterval.setObjectName(u"le_timeinterval")
        self.le_timeinterval.setMinimumSize(QSize(240, 0))
#Scroll area
        self.scroll_markers =QScrollArea(self.centralwidget)
        self.scroll_markers.setObjectName(u"scroll_markers")
        self.scroll_markers.setVerticalScrollBarPolicy(False)
#Spacers
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalSpacer_3 = QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
#Spinboxes
        self.sb_cutoff = QSpinBox(self.centralwidget)
        self.sb_cutoff.setObjectName(u"sb_cutoff")
        self.sb_cutoff.setMaximum(999999999)
        self.sb_refractair = QDoubleSpinBox(self.centralwidget)
        self.sb_refractair.setObjectName(u"sb_refractair")
        self.sb_refractair.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom))
        self.sb_refractair.setDecimals(3)
        self.sb_refractair.setSingleStep(0.001)
        self.sb_refractair.setValue(0.005)
#Tab widget
        self.plt_container = QTabWidget(self.centralwidget)
        self.plt_container.setObjectName(u"plt_container")
#Add to grid layout
        self.gridLayout.addWidget(self.plt_container, 0, 0, 13, 4)
        self.gridLayout.addWidget(self.lbl_file, 13, 0, 1, 1)
        self.gridLayout.addWidget(self.ccb_channels, 14, 0, 1, 2)
        self.gridLayout.addWidget(self.lbl_condition, 15, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_output, 16, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_refractair, 17, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_thresholds, 18, 0, 1, 1)
        self.gridLayout.addWidget(self.cb_cutoff, 19, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_timeinterval, 20, 0, 1, 1)
        
        self.gridLayout.addWidget(self.comb_file, 13, 1, 1, 1)
        self.gridLayout.addWidget(self.le_condition, 15, 1, 1, 1)
        self.gridLayout.addWidget(self.le_outputname, 16, 1, 1, 1)
        self.gridLayout.addWidget(self.sb_refractair, 17, 1, 1, 1)
        self.gridLayout.addWidget(self.le_thresholds, 18, 1, 1, 1)
        self.gridLayout.addWidget(self.sb_cutoff, 19, 1, 1, 1)
        self.gridLayout.addWidget(self.le_timeinterval, 20, 1, 1, 1)
        
        self.gridLayout.addWidget(self.bt_file, 13, 2, 1, 1)
        self.gridLayout.addWidget(self.scroll_markers, 18, 2, 3, 2)
        self.scroll_markers.setWidget(self.lbl_markers)
        
        self.gridLayout.addItem(self.horizontalSpacer_2, 13, 3, 1, 1)
        
        self.gridLayout.addWidget(self.cb_selectall, 0, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_wholerecording, 1, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_selectedframes, 2, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_spikesorting, 3, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_averagewaveform, 4, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_interspikeinterval, 5, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_amplitudedistribution, 6, 4, 1, 1)
        self.gridLayout.addItem(self.verticalSpacer_3, 7, 4, 1, 1)
        self.gridLayout.addWidget(self.cb_externalplot, 8, 4, 1, 1)
        self.gridLayout.addWidget(self.bt_go, 9, 4, 1, 1)
        self.gridLayout.addWidget(self.bt_closeplots, 10, 4, 1, 1)
        self.gridLayout.addItem(self.verticalSpacer, 12, 4, 1, 1)
        self.gridLayout.addWidget(self.bt_saveall, 13, 4, 1, 1)
        self.gridLayout.addWidget(self.bt_quit, 20, 4, 1, 1)
#Add everything to mainwindow
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        MainWindow.setMenuBar(self.menubar)
        self.menubar.addAction(self.menuMenu.menuAction())
        self.menuMenu.addAction(self.actionOpen_file)

        self.retranslateUi(MainWindow)
        self.bt_quit.clicked.connect(MainWindow.close)

        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.cb_selectedframes.setText(QCoreApplication.translate("MainWindow", u"Selected time frames", None))
        self.lbl_output.setText(QCoreApplication.translate("MainWindow", u"Output", None))
        self.le_condition.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Condition name", None))
        self.cb_interspikeinterval.setText(QCoreApplication.translate("MainWindow", u"Interspike interval", None))
        self.cb_wholerecording.setText(QCoreApplication.translate("MainWindow", u"Whole recording", None))
        self.cb_externalplot.setText(QCoreApplication.translate("MainWindow", u"Plot in external windows", None))
        self.cb_cutoff.setText(QCoreApplication.translate("MainWindow", u"Cut off threshold", None))
        self.cb_averagewaveform.setText(QCoreApplication.translate("MainWindow", u"Average waveform", None))
        self.lbl_timeinterval.setText(QCoreApplication.translate("MainWindow", u"Time intervals", None))
        self.lbl_markers.setText(QCoreApplication.translate("MainWindow", u"", None))
        self.le_timeinterval.setToolTip(QCoreApplication.translate("MainWindow",
u"Format: [Start time 1] to [Stop time 2] and [Start time 2] to [Stop time 2] etc.\n"
"e.g. 1: marker 1 to 61 and 120 to marker 2\n"
"e.g. 2:1 to 60\n"
"e.g. 3:marker 1 to marker 3\n"
"marker can be denoted with m, capital letters possible, ", None))
        self.le_timeinterval.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Time intervals in seconds or by marker", None))
        self.cb_spikesorting.setText(QCoreApplication.translate("MainWindow", u"Spike sorting", None))
        self.lbl_file.setText(QCoreApplication.translate("MainWindow", u"File", None))
        self.cb_amplitudedistribution.setText(QCoreApplication.translate("MainWindow", u"Amplitude distribution", None))
        self.le_thresholds.setToolTip(QCoreApplication.translate("MainWindow",
u"Format: [Threshold 1], [Threshold 2], [Threshold 3], etc.\n"
"e.g. 1: 700,1200,4000\n"
"e.g. 2: 700 1200 1400\n"
"Spacers between thresholds can be a comma or space ", None))
        self.le_thresholds.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Thresholds in a.u.", None))
        self.bt_file.setText(QCoreApplication.translate("MainWindow", u"View raw data", None))
        self.lbl_condition.setText(QCoreApplication.translate("MainWindow", u"Condition", None))
        self.bt_closeplots.setText(QCoreApplication.translate("MainWindow", u"Close all plots", None))
        self.bt_go.setText(QCoreApplication.translate("MainWindow", u"Run selected", None))
        self.lbl_thresholds.setText(QCoreApplication.translate("MainWindow", u"Thresholds", None))
        self.cb_selectall.setText(QCoreApplication.translate("MainWindow", u"Select all", None))
        self.bt_saveall.setText(QCoreApplication.translate("MainWindow", u"Save selected data and plots", None))
        self.bt_quit.setText(QCoreApplication.translate("MainWindow", u"Quit", None))
        self.lbl_refractair.setText(QCoreApplication.translate("MainWindow", u"Distance Between peaks", None))
        self.menuMenu.setTitle(QCoreApplication.translate("MainWindow", u"Menu", None))
        self.actionOpen_file.setText(QCoreApplication.translate("MainWindow", u"Open file...", None))
    # retranslateUi
        self.plt_container.setTabsClosable(True)
        self.scroll_markers.setFrameShape(QFrame.NoFrame)
        self.scroll_markers.setWidgetResizable(True)
        self.scroll_markers.setMinimumHeight(10)
    
if __name__ == "__main__":
    import sys
    class Main(QMainWindow, Ui_MainWindow):
        def __init__(self):
            super(Main, self).__init__()
            self.setupUi(self)
            
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    ui = Main()
    ui.show()
    sys.exit(app.exec())