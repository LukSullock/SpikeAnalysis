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
import os
import numpy as np
from PyQt5.QtCore import (QCoreApplication, QSize, QMetaObject,
                          QRect, Qt, QEvent, QLocale)
from PyQt5.QtGui import (QStandardItem, QBrush, QColor)
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QMenu,
                        QLabel, QLineEdit, QMenuBar, QPushButton, QAction,
                        QSizePolicy, QSpacerItem, QSpinBox, QTabWidget,
                        QWidget, QApplication,QMainWindow, QDoubleSpinBox,
                        QScrollArea, QFrame, QStatusBar, QProgressBar,
                        QDialog, QDialogButtonBox, QFormLayout)

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

class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.parent=parent
        self.low=QSpinBox(self)
        self.high=QSpinBox(self)
        self.notch=QSpinBox(self)
        self.save=QPushButton(self, text="Save filtered signal")
        self.low.setMinimum(1)
        self.high.setMinimum(1)
        self.notch.setMinimum(1)
        self.low.setMaximum(2147483647)
        self.high.setMaximum(2147483647)
        self.notch.setMaximum(2147483647)
        self.high.setValue(500)
        self.notch.setValue(50)
        self.cb_low=QCheckBox(self, text="Bandpass filter low (Hz)")
        self.cb_high=QCheckBox(self, text="Bandpass filter high (Hz)")
        self.cb_notch=QCheckBox(self, text="50Hz notch filter")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);

        if parent:
            self.low.setValue(self.parent.lowpass)
            self.high.setValue(self.parent.highpass)
            self.notch.setValue(self.parent.notchv)
            if self.parent.bandfilter:
                self.cb_low.setChecked(True)
                self.cb_high.setChecked(True)
            if self.parent.bandfilter:
                self.cb_notch.setChecked(True)
        
        layout = QFormLayout(self)
        layout.addRow(self.cb_low, self.low)
        layout.addRow(self.cb_high, self.high)
        layout.addRow(self.cb_notch, self.notch)
        layout.addRow(self.save, buttonBox)
        
        buttonBox.accepted.connect(self.getInputs)
        buttonBox.rejected.connect(self.close)
        self.cb_low.stateChanged.connect(self.CheckAll)
        self.cb_high.stateChanged.connect(self.CheckAll)
        self.save.clicked.connect(self.SaveSignal)
    
    def SaveSignal(self):
        datafilt=self.parent.filter_data(self.parent.data, self.parent.framerate,
                            low=self.low.value(), high=self.high.value(), 
                            notch=self.notch.value(), order=2, 
                            notchfilter=self.cb_notch.isChecked(), 
                            bandfilter=self.cb_low.isChecked())
        file = os.path.join(f"{os.getcwd()}/data", f'{str(self.parent.comb_file.currentText()[:-4])}_filt.npz')
        markername =f"{str(self.parent.comb_file.currentText()[:-4])}-events.txt"
        markernew =f"{str(self.parent.comb_file.currentText()[:-4])}_filt-events.txt"
        markerfile=os.path.join(f"{os.getcwd()}/data", markername)
        markerfilenew=os.path.join(f"{os.getcwd()}/data", markernew)
        with open(file,"wb") as f:
            np.savez(f, sf=self.parent.framerate, data=np.swapaxes(datafilt,0,1))
        try:
            with open(markerfile, encoding="utf8") as csvfile:
                markersCSV=csvfile.read()
            with open(markerfilenew,"w", encoding="utf-8") as csvfile:
                csvfile.write(markersCSV)
        except FileNotFoundError:
            pass
        
        self.parent.InfoMsg("Saved filtered data.", f'Data can be found at:\n{file}')
        
    
    def CheckAll(self, sender):
        check=bool(sender)
        self.cb_low.stateChanged.disconnect()
        self.cb_high.stateChanged.disconnect()
        self.cb_low.setChecked(check)
        self.cb_high.setChecked(check)
        self.cb_low.stateChanged.connect(self.CheckAll)
        self.cb_high.stateChanged.connect(self.CheckAll)
        
    def getInputs(self):
        if self.cb_low.isChecked():
            self.parent.bandfilter=True
            self.parent.lowpass=self.low.value()
            self.parent.highpass=self.high.value()
        if self.cb_notch.isChecked():
            self.parent.notchfilter=True
            self.parent.notchv=self.notch.value()
        self.close()
    
class crosscorrDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.parent=parent
        self.channel1=QComboBox(self)
        self.channel2=QComboBox(self)
        self.cluster1=QComboBox(self)
        self.cluster2=QComboBox(self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self);
        if parent:
            channels=str(self.parent.ccb_channels.currentText()).split(", ")
            self.channel1.addItems(channels)
            markersN=self.parent.markers.keys()
            markers=[f"Marker {mark}" for mark in markersN]
            self.channel1.addItems(markers)
            self.channel2.addItems(channels)
            self.clusters=[[] for _ in range(len(channels))]
            for ii, ch in enumerate(self.parent.clusters):
                for cl in ch:
                    self.clusters[ii].append(cl[4])
        layout = QFormLayout(self)
        layout.addRow(self.channel1, self.cluster1)
        layout.addRow(self.channel2, self.cluster2)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.getInputs)
        self.channel1.currentIndexChanged.connect(self.channelChange1)
        self.channel2.currentIndexChanged.connect(self.channelChange2)
        self.channelChange1()
        self.channelChange2()
        
    def channelChange1(self):
        channelindx=self.channel1.currentIndex()
        for ii in reversed(range(self.cluster1.count())):
            self.cluster1.removeItem(ii)
        if "Channel" in self.channel1.currentText():
            self.cluster1.addItems(self.clusters[channelindx])
    def channelChange2(self):
        channelindx=self.channel1.currentIndex()
        for ii in reversed(range(self.cluster2.count())):
            self.cluster2.removeItem(ii)
        self.cluster2.addItems(self.clusters[channelindx])
        
    def getInputs(self):
        if "Channel" in self.channel1.currentText():
            self.parent.x1=[self.channel1.currentIndex(), self.cluster1.currentIndex()]
        elif "Marker" in self.channel1.currentText():
            markerN=float(self.channel1.currentText().split("Marker ")[-1])
            self.parent.x1=[self.channel1.currentText(), self.parent.markers[markerN]]
        self.parent.x2=[self.channel2.currentIndex(), self.cluster2.currentIndex()]
        self.close()
            
        
class Ui_MainWindow(object):
    def openFilterDialog(self):
        try:
            self.filtdialog=FilterDialog(self)
        except:
            return
        self.filtdialog.show()
        
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
        self.actionBatchana = QAction(MainWindow)
        self.actionBatchana.setObjectName(u"actionBatchana")
        self.actionLivePlot = QAction(MainWindow)
        self.actionLivePlot.setObjectName(u"actionLivePlot")
        self.actionLivePlot.setCheckable(True)
        self.actionFilters = QAction(MainWindow)
        self.actionFilters.setObjectName(u"actionFilters")
        self.actionOpen_file.setEnabled(False)
        #self.actionFilters.setEnabled(False)
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
        self.bt_setsettings = QPushButton(self.centralwidget)
        self.bt_setsettings.setObjectName(u"bt_saveall")
        self.bt_setsettings.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.bt_updatefile = QPushButton(self.centralwidget)
        self.bt_updatefile.setObjectName(u"bt_updatefile")
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
        self.cb_rawrecording = QCheckBox(self.centralwidget)
        self.cb_rawrecording.setObjectName(u"cb_rawrecording")
        self.cb_autocorr = QCheckBox(self.centralwidget)
        self.cb_autocorr.setObjectName(u"cb_autocorr")
        self.cb_crosscorr = QCheckBox(self.centralwidget)
        self.cb_crosscorr.setObjectName(u"cb_crosscorr")
        self.cb_powerfreq = QCheckBox(self.centralwidget)
        self.cb_powerfreq.setObjectName(u"cb_powerfreq")
        self.cb_erp = QCheckBox(self.centralwidget)
        self.cb_erp.setObjectName(u"cb_erp")
        self.cb_flipdata = QCheckBox(self.centralwidget)
        self.cb_flipdata.setObjectName(u"cb_flipdata")
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
        self.lbl_erpminmax = QLabel(self.centralwidget)
        self.lbl_erpminmax.setObjectName(u"lbl_erpminmax")
        # self.lbl_snr = QLabel(self.centralwidget)
        # self.lbl_snr.setObjectName(u"lbl_snr")
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
#Progressbar
        self.progressBar = QProgressBar()
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
        self.sb_cutoff.setMaximum(2147483647)
        self.sb_cutoff.setMinimum(1)
        self.sb_refractair = QDoubleSpinBox(self.centralwidget)
        self.sb_refractair.setObjectName(u"sb_refractair")
        self.sb_refractair.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom))
        self.sb_refractair.setDecimals(2)
        self.sb_refractair.setSingleStep(0.01)
        self.sb_refractair.setValue(0.80)
        self.sb_refractair.setMinimum(0.5)
        self.sb_refractair.setMaximum(1.0)
        self.sb_erpmin=QDoubleSpinBox(self.centralwidget)
        self.sb_erpmin.setObjectName(u"sb_erpmin")
        self.sb_erpmin.setSingleStep(0.001)
        self.sb_erpmin.setDecimals(3)
        self.sb_erpmin.setValue(1)
        self.sb_erpmax=QDoubleSpinBox(self.centralwidget)
        self.sb_erpmax.setObjectName(u"sb_erpmax")
        self.sb_erpmax.setSingleStep(0.001)
        self.sb_erpmax.setDecimals(3)
        self.sb_erpmax.setValue(5)
#Tab widget
        self.plt_container = QTabWidget(self.centralwidget)
        self.plt_container.setObjectName(u"plt_container")
#Add to grid layout
        self.gridLayout.addWidget(self.plt_container, 0, 0, 20, 6)
        self.gridLayout.addWidget(self.lbl_file, 20, 0, 1, 1)
        self.gridLayout.addWidget(self.ccb_channels, 21, 0, 1, 3)
        self.gridLayout.addWidget(self.lbl_condition, 22, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_output, 23, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_refractair, 24, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_thresholds, 25, 0, 1, 1)
        self.gridLayout.addWidget(self.cb_cutoff, 26, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_timeinterval, 27, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_erpminmax, 28, 0, 1, 1)
        
        self.gridLayout.addWidget(self.comb_file, 20, 1, 1, 2)
        self.gridLayout.addWidget(self.le_condition, 22, 1, 1, 2)
        self.gridLayout.addWidget(self.le_outputname, 23, 1, 1, 2)
        self.gridLayout.addWidget(self.sb_refractair, 24, 1, 1, 2)
        self.gridLayout.addWidget(self.le_thresholds, 25, 1, 1, 2)
        self.gridLayout.addWidget(self.sb_cutoff, 26, 1, 1, 2)
        self.gridLayout.addWidget(self.le_timeinterval, 27, 1, 1, 2)
        self.gridLayout.addWidget(self.sb_erpmin, 28,1,1,1)
        
        self.gridLayout.addWidget(self.sb_erpmax, 28,2,1,1)
        
        self.gridLayout.addWidget(self.bt_updatefile, 20, 3, 1, 1)
        
        self.gridLayout.addWidget(self.bt_file, 21, 3, 1, 1)
        self.gridLayout.addWidget(self.cb_flipdata, 22, 3, 1, 1)
        self.gridLayout.addWidget(self.bt_setsettings, 25, 3, 3, 1)
        
        # self.gridLayout.addWidget(self.lbl_snr, 20, 4, 1, 1)
        self.gridLayout.addWidget(self.scroll_markers, 25, 4, 3, 2)
        self.scroll_markers.setWidget(self.lbl_markers)
        
        self.gridLayout.addItem(self.horizontalSpacer_2, 20, 5, 1, 1)
        
        self.gridLayout.addWidget(self.cb_selectall, 0, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_rawrecording, 1, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_selectedframes, 2, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_spikesorting, 3, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_averagewaveform, 4, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_interspikeinterval, 5, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_amplitudedistribution, 6, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_autocorr, 7, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_crosscorr, 8, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_powerfreq, 9, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_erp, 10, 6, 1, 1)
        self.gridLayout.addItem(self.verticalSpacer_3, 12, 6, 1, 1)
        self.gridLayout.addWidget(self.cb_externalplot, 13, 6, 1, 1)
        self.gridLayout.addWidget(self.bt_go, 14, 6, 1, 1)
        self.gridLayout.addWidget(self.bt_saveall, 15, 6, 1, 1)
        self.gridLayout.addWidget(self.bt_closeplots, 16, 6, 1, 1)
        self.gridLayout.addItem(self.verticalSpacer, 17, 6, 1, 1)
        self.gridLayout.addWidget(self.bt_quit, 28, 6, 1, 1)
        
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
        self.menuMenu.addAction(self.actionFilters)
        self.menuMenu.addAction(self.actionBatchana)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionLivePlot)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.progressBar)

        self.retranslateUi(MainWindow)
        self.bt_quit.clicked.connect(MainWindow.close)

        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.cb_selectedframes.setText(QCoreApplication.translate("MainWindow", u"Selected time frames", None))
        self.lbl_output.setText(QCoreApplication.translate("MainWindow", u"Output", None))
        self.le_condition.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Condition name", None))
        self.cb_interspikeinterval.setText(QCoreApplication.translate("MainWindow", u"Interspike interval", None))
        self.cb_rawrecording.setText(QCoreApplication.translate("MainWindow", u"Raw recording", None))
        self.cb_externalplot.setText(QCoreApplication.translate("MainWindow", u"Plot in external windows", None))
        self.cb_cutoff.setText(QCoreApplication.translate("MainWindow", u"Cut off threshold", None))
        self.cb_averagewaveform.setText(QCoreApplication.translate("MainWindow", u"Average waveform", None))
        self.cb_erp.setText(QCoreApplication.translate("MainWindow", u"Event-Related Potential", None))
        self.cb_crosscorr.setText(QCoreApplication.translate("MainWindow", u"Crosscorrelogram", None))
        self.cb_autocorr.setText(QCoreApplication.translate("MainWindow", u"Autocorrelogram", None))
        self.cb_powerfreq.setText(QCoreApplication.translate("MainWindow", u"Spectrogram", None))
        self.lbl_timeinterval.setText(QCoreApplication.translate("MainWindow", u"Time intervals", None))
        self.lbl_markers.setText(QCoreApplication.translate("MainWindow", u"", None))
        self.lbl_erpminmax.setText(QCoreApplication.translate("MainWindow", u"Time (s) before and after ERP", None))
        self.le_timeinterval.setToolTip(QCoreApplication.translate("MainWindow",
u"Format: [Start time 1] to [Stop time 2] and [Start time 2] to [Stop time 2] etc.\n"
"e.g. 1: marker 1 to 61 and 120 to marker 2\n"
"e.g. 2: 1 to 60\n"
"e.g. 3: marker 1 to marker 3\n"
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
        self.bt_file.setText(QCoreApplication.translate("MainWindow", u"View whole recording", None))
        self.bt_updatefile.setText(QCoreApplication.translate("MainWindow", u"Update file list", None))
        self.cb_flipdata.setText(QCoreApplication.translate("MainWindow", u"Flip data", None))
        self.lbl_condition.setText(QCoreApplication.translate("MainWindow", u"Condition", None))
        self.bt_closeplots.setText(QCoreApplication.translate("MainWindow", u"Close all plots", None))
        self.bt_go.setText(QCoreApplication.translate("MainWindow", u"Run selected", None))
        self.lbl_thresholds.setText(QCoreApplication.translate("MainWindow", u"Thresholds", None))
        self.cb_selectall.setText(QCoreApplication.translate("MainWindow", u"Select all", None))
        self.bt_saveall.setText(QCoreApplication.translate("MainWindow", u"Run and save selected", None))
        self.bt_setsettings.setText(QCoreApplication.translate("MainWindow", u"Set thresholds and\ntime frames", None))
        self.bt_quit.setText(QCoreApplication.translate("MainWindow", u"Quit", None))
        self.lbl_refractair.setText(QCoreApplication.translate("MainWindow", u"Percentage of threshold for new spike", None))
        self.menuMenu.setTitle(QCoreApplication.translate("MainWindow", u"Menu", None))
        self.actionOpen_file.setText(QCoreApplication.translate("MainWindow", u"Open file...", None))
        self.actionBatchana.setText(QCoreApplication.translate("MainWindow", u"Batch analysis", None))
        self.actionLivePlot.setText(QCoreApplication.translate("MainWindow", u"Plot selections live", None))
        self.actionFilters.setText(QCoreApplication.translate("MainWindow", u"Set filters", None))
    # retranslateUi
        self.plt_container.setTabsClosable(True)
        self.scroll_markers.setFrameShape(QFrame.NoFrame)
        self.scroll_markers.setWidgetResizable(True)
        self.scroll_markers.setMinimumHeight(10)
        self.actionFilters.triggered.connect(self.openFilterDialog)
    #Filter defaults
        self.bandfilter=False
        self.notchfilter=False
        self.lowpass=1
        self.highpass=500
        self.notchv=50
    
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