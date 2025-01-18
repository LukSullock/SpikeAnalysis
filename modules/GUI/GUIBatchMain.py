# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 16:52:20 2024

@author: LukSu
"""
from PyQt5.QtCore import (QCoreApplication, QMetaObject)
from PyQt5.QtWidgets import (QGridLayout, QLabel, QLineEdit, QPushButton,
                             QWidget, QMessageBox, QCheckBox, QSpinBox)
from modules.batchrun.BatchFunctions import (RunBatch, SaveBatch)

class BatchWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.layout=QGridLayout()
        self.lbl_chtime=QLabel()
        self.lbl_chtime.setObjectName(u"lbl_chtime")
        self.lbl_thresholds = QLabel()
        self.lbl_thresholds.setObjectName(u"lbl_thresholds")
        self.lbl_cutoffs=QLabel()
        self.lbl_chtime.setObjectName(u"lbl_cutoffs")
        self.btn_cancelbatch = QPushButton()
        self.btn_cancelbatch.setObjectName(u"btn_cancelbatch")
        self.btn_runbatch = QPushButton()
        self.btn_runbatch.setObjectName(u"btn_runbatch")
        self.btn_savebatch = QPushButton()
        self.btn_savebatch.setObjectName(u"btn_savebatch")
        
        file=str(parent.comb_file.currentText())
        if file=="Select file":
            _=parent.ErrorMsg("Please select a datafile")
            self.close()
            return False
        if not "Select" in str(parent.ccb_channels.currentText()):
            channels=str(parent.ccb_channels.currentText()).split(", ")
        else:
            _=parent.ErrorMsg("Please select atleast 1 channel.")
            self.close()
            return False
        times=str(parent.le_timeinterval.text())
        times=times.split(" and ")
        for ii,art in enumerate(times):
            times[ii]=art.split(" to ")
        if not all([all(interval) for interval in times]) or any([len(interval)<2 for interval in times]):
            _=parent.ErrorMsg("Please check time intervals")
            self.close()
            return False
        self.start_time,self.stop_time=parent.gettimestamps(parent, times)
        channels=[int(chan.split("Channel ")[-1]) for chan in str(parent.ccb_channels.currentText()).split(", ")]
        
        self.lbl_chtimeframes=[]
        self.le_thresholds=[]
        self.cb_cutoffs=[]
        self.sb_cutoffs=[]
        cntr=0
        for ch in channels:
            for ii,sttime in enumerate(self.start_time):
                self.lbl_chtimeframes.append(QLabel())
                self.lbl_chtimeframes[cntr].setObjectName(u"lbl_chtimeframes")
                self.le_thresholds.append(QLineEdit())
                self.le_thresholds[cntr].setObjectName(u"le_thresholds")
                self.cb_cutoffs.append(QCheckBox())
                self.cb_cutoffs[cntr].setObjectName(u"cb_cutoffs")
                self.sb_cutoffs.append(QSpinBox())
                self.sb_cutoffs[cntr].setObjectName(u"sb_cutoffs")
                self.sb_cutoffs[cntr].setMaximum(999999999)
                self.sb_cutoffs[cntr].setMinimum(1)
                cntr+=1
                
        self.layout.addWidget(self.lbl_chtime, 0,0,1,1)
        self.layout.addWidget(self.lbl_thresholds, 0,1,1,1)
        self.layout.addWidget(self.lbl_cutoffs, 0,2,1,2)
        for ii in range(len(self.le_thresholds)):
            self.layout.addWidget(self.le_thresholds[ii], ii+1,1,1,1)
            self.layout.addWidget(self.lbl_chtimeframes[ii], ii+1,0,1,1)
            self.layout.addWidget(self.cb_cutoffs[ii], ii+1,2,1,1)
            self.layout.addWidget(self.sb_cutoffs[ii], ii+1,3,1,1)
        
        self.layout.addWidget(self.btn_cancelbatch, len(self.lbl_chtimeframes)+1,0,1,1)
        self.layout.addWidget(self.btn_runbatch, len(self.lbl_chtimeframes)+1,1,1,1)
        self.layout.addWidget(self.btn_savebatch, len(self.lbl_chtimeframes)+1,2,1,2)
        self.retranslateUi(parent)

        QMetaObject.connectSlotsByName(self)
        
        self.setLayout(self.layout)
        self.btn_cancelbatch.clicked.connect(self.close)
        self.btn_runbatch.clicked.connect(lambda: RunBatch(self, parent))
        self.btn_savebatch.clicked.connect(lambda: SaveBatch(self, parent))

    def retranslateUi(self, parent):
        """Adds text, tooltips, etc. to the UI"""
        self.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.lbl_chtime.setText(QCoreApplication.translate("Form", u"Channel and timeframe", None))
        self.lbl_thresholds.setText(QCoreApplication.translate("Form", u"Thresholds", None))
        self.lbl_cutoffs.setText(QCoreApplication.translate("Form", u"Cutoff threshold", None))
        self.btn_cancelbatch.setText(QCoreApplication.translate("Form", u"Cancel", None))
        self.btn_runbatch.setText(QCoreApplication.translate("Form", u"Run batch", None))
        self.btn_savebatch.setText(QCoreApplication.translate("Form", u"Save and run batch", None))
        channels=str(parent.ccb_channels.currentText()).split(", ")
        cntr=0
        for ch in channels:
            for ii,sttime in enumerate(self.start_time):
                string=str(parent.le_thresholds.text())
                self.le_thresholds[cntr].setText(QCoreApplication.translate("Form", string, None))
                self.le_thresholds[cntr].setToolTip(QCoreApplication.translate("MainWindow",
u"Format: [Threshold 1], [Threshold 2], [Threshold 3], etc.\n"
"Spacers between thresholds can be a comma or space.\n"
"Multiple thresholds can be set by enclosing all thresholds in brackets and seperating batches with a semicolon\n"
"e.g.: [700,1200;800,1300] creates figures for the thresholds 700 with 1200 and for 800 with 1300", None))
                self.le_thresholds[cntr].setPlaceholderText(QCoreApplication.translate("MainWindow", u"Thresholds in a.u.", None))
                string=f"{ch}: {sttime} to {self.stop_time[ii]}"
                self.lbl_chtimeframes[cntr].setText(QCoreApplication.translate("Form", string, None))
                cntr+=1
        if parent.cb_cutoff.isChecked():
            for ii in range(len(self.cb_cutoffs)):
                self.cb_cutoffs[ii].setChecked(True)
                self.sb_cutoffs[ii].setValue(int(parent.sb_cutoff.text()))
                
            
    def checks(self,parent):
        """
        Function to check if all the mandatory variables are filled in.

        Parameters
        ----------
        parent : class
            Reference to the main GUI.

        Returns
        -------
        channels : string
            Returns False if a check is not met, otherwise returns the string of the selected channels.

        """
        file=str(parent.comb_file.currentText())
        if file=="Select file":
            parent.ErrorMsg("Please select a datafile")
            return False
        if not "Select" in str(parent.ccb_channels.currentText()):
            channels=str(parent.ccb_channels.currentText()).split(", ")
        else:
            parent.ErrorMsg("Please select a channel.")
            return False
        if len(str(parent.le_thresholds.text()))==0:
            reply=parent.WarningContinue("No thresholds set. Do you wish to continue?", "Warning, this will likely take a while to process.")
            if reply==QMessageBox.No: return False
        return channels