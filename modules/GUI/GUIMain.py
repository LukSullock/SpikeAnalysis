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
import sys
import matplotlib.pyplot as plt
from matplotlib.colors import TABLEAU_COLORS
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from modules.GUI.Ui_SpikeSorting import Ui_MainWindow
import modules.GUI.GUIFunctions as GUIFunctions
from modules.GUI.GUIBatchMain import BatchWidget

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, *, RunSortingfnc, SavePlotsfnc, ViewWholefnc, ThrChangefnc,
                 CutoffChangefnc, IntervalChangefnc, GetTimeStampsfnc, UpdateWholePlotfnc):
        super(Main, self).__init__()
        self.setupUi(self)
        self.colorSTR=TABLEAU_COLORS
        self.canvassen=[]
        self.canvasboxes=[]
        self.threshlines=[]
        self.cutoffrec=[]
        self.intervals=[]
        self.text=""
        self.bandfilter=False
        self.notchfilter=False
        self.lowpass=1
        self.highpass=500
        self.notchv=50
        
        self.RunSorting=RunSortingfnc
        self.SavePlots=SavePlotsfnc
        self.viewWhole=ViewWholefnc
        self.ThresholdChange=ThrChangefnc
        self.CutoffChange=CutoffChangefnc
        self.IntervalChange=IntervalChangefnc
        self.gettimestamps=GetTimeStampsfnc
        self.UpdateWholePlot=UpdateWholePlotfnc
        
        #Connect functions
        self.bt_updatefile.clicked.connect(self.CheckFiles)
        self.CheckFiles()
        self.comb_file.activated.connect(self.dataloadplot)
        self.dataloadplot()
        self.cb_selectall.stateChanged.connect(self.select_all)
        self.cb_rawrecording.stateChanged.connect(self.deselect_select_all)
        self.cb_selectedframes.stateChanged.connect(self.deselect_select_all)
        self.cb_spikesorting.stateChanged.connect(self.deselect_select_all)
        self.cb_averagewaveform.stateChanged.connect(self.deselect_select_all)
        self.cb_interspikeinterval.stateChanged.connect(self.deselect_select_all)
        self.cb_amplitudedistribution.stateChanged.connect(self.deselect_select_all)
        self.cb_autocorr.stateChanged.connect(self.deselect_select_all)
        self.cb_crosscorr.stateChanged.connect(self.deselect_select_all)
        self.cb_powerfreq.stateChanged.connect(self.deselect_select_all)
        self.cb_erp.stateChanged.connect(self.deselect_select_all)
        self.ccb_channels.currentTextChanged.connect(self.OutputNameChange)
        self.le_condition.textEdited.connect(self.OutputNameChange)
        self.plt_container.currentChanged.connect(self.tab_change)
        self.bt_go.clicked.connect(lambda: self.RunSorting(self))
        self.bt_saveall.clicked.connect(lambda: self.SavePlots(self))
        self.bt_closeplots.clicked.connect(self.closePlots)
        self.bt_file.clicked.connect(lambda: self.viewWhole(self))
        self.plt_container.tabCloseRequested.connect(lambda indx: self.closeTab(indx))
        self.actionBatchana.triggered.connect(self.BatchWindow)
        self.bt_setsettings.clicked.connect(lambda: self.UpdateWholePlot(self))
        self.actionLivePlot.triggered.connect(self.LiveUpdate)
        self.le_timeinterval.returnPressed.connect(lambda: self.IntervalChange(self))
        self.le_thresholds.returnPressed.connect(lambda: self.ThresholdChange(self))
        self.sb_cutoff.lineEdit().returnPressed.connect(lambda: self.CutoffChange(self))
    
    def BatchWindow(self):
        try:
           self.batchwidget=BatchWidget(self)
        except:
           return
        self.batchwidget.show()
        
    def closeTab(self, indx):
        self.plt_container.removeTab(indx)
        self.canvassen.pop(indx)
        self.canvasboxes.pop(indx)
    def closePlots(self):
        plt.close("all")
        self.canvassen=[]
        self.canvasboxes=[]
        self.plt_container.clear()
    
    def LiveUpdate(self):
        if self.actionLivePlot.isChecked():
            self.le_timeinterval.returnPressed.disconnect()
            self.le_thresholds.returnPressed.disconnect()
            self.sb_cutoff.lineEdit().returnPressed.disconnect()
            self.le_timeinterval.textChanged.connect(lambda: self.IntervalChange(self))
            self.le_thresholds.textChanged.connect(lambda: self.ThresholdChange(self))
            self.sb_cutoff.valueChanged.connect(lambda: self.CutoffChange(self))
            self.cb_cutoff.stateChanged.connect(lambda: self.CutoffChange(self))
        else:
            self.le_timeinterval.textChanged.disconnect()
            self.le_thresholds.textChanged.disconnect()
            self.sb_cutoff.valueChanged.disconnect()
            self.cb_cutoff.stateChanged.disconnect()
            self.le_timeinterval.returnPressed.connect(lambda: self.IntervalChange(self))
            self.le_thresholds.returnPressed.connect(lambda: self.ThresholdChange(self))
            self.sb_cutoff.lineEdit().returnPressed.connect(lambda: self.CutoffChange(self))
    
    def tab_change(self):
        indx=self.plt_container.currentIndex()
        file=self.plt_container.tabText(indx).split(":")
        if file[0]:
            if "Whole" in file[1]:
                self.comb_file.setCurrentText(file[0])
                if len(self.canvassen[indx][0].axs)!=self.ccb_channels.count()-1:
                    for ii in reversed(range(self.ccb_channels.count())):
                        if ii!=0:
                            self.ccb_channels.removeItem(ii)
                    self.ccb_channels.addItems([f"Channel {ii+1}" for ii in range(len(self.canvassen[indx][0].axs))])
    
    def deselect_select_all(self):
        self.cb_selectall.stateChanged.disconnect(self.select_all)
        if all([self.cb_rawrecording.isChecked(), self.cb_selectedframes.isChecked(), 
               self.cb_spikesorting.isChecked(), self.cb_averagewaveform.isChecked(),
               self.cb_interspikeinterval.isChecked(), self.cb_amplitudedistribution.isChecked(),
               self.cb_autocorr.isChecked(), self.cb_crosscorr.isChecked(),
               self.cb_powerfreq.isChecked(), self.cb_erp.isChecked()]):
            self.cb_selectall.setChecked(True)
        elif not all([self.cb_rawrecording.isChecked(), self.cb_selectedframes.isChecked(), 
               self.cb_spikesorting.isChecked(), self.cb_averagewaveform.isChecked(),
               self.cb_interspikeinterval.isChecked(), self.cb_amplitudedistribution.isChecked(),
               self.cb_autocorr.isChecked(), self.cb_crosscorr.isChecked(),
               self.cb_powerfreq.isChecked(), self.cb_erp.isChecked()]):
            self.cb_selectall.setChecked(False)
        self.cb_selectall.stateChanged.connect(self.select_all)
    def select_all(self):
        state=self.cb_selectall.isChecked()
        self.cb_rawrecording.setChecked(state)
        self.cb_selectedframes.setChecked(state)
        self.cb_spikesorting.setChecked(state)
        self.cb_averagewaveform.setChecked(state)
        self.cb_interspikeinterval.setChecked(state)
        self.cb_amplitudedistribution.setChecked(state)
        self.cb_autocorr.setChecked(state)
        self.cb_crosscorr.setChecked(state)
        self.cb_powerfreq.setChecked(state)
        self.cb_erp.setChecked(state)
        
    def CheckFiles(self):
        #Update combobox with file options
        files=os.listdir("data")
        for ii in reversed(range(len(files))):
            if ".wav" not in files[ii]:
                if ".mat" not in files[ii]: ####temporary
                    del files[ii]
        #First disconnect function to be able to update combobox list, then reconnect function
        if len(files)+1!=self.comb_file.count():
            for ii in reversed(range(self.comb_file.count())):
                if ii!=0:
                    self.comb_file.removeItem(ii)
            #self.comb_file.clear()
            #self.comb_file.addItem("Select file")
            self.comb_file.addItems(files)
        self.OutputNameChange()
    def dataloadplot(self):
        if self.text!=str(self.comb_file.currentText()):
            self.text=f'{str(self.comb_file.currentText())}'
            if ".wav" in self.text or ".mat" in self.text:
                self.viewWhole(self)
    def OutputNameChange(self):
        if ".wav" not in str(self.comb_file.currentText()):
            self.le_outputname.setText("")
            return
        text=self.text[:-4]
        #if not "Select" in str(self.ccb_channels.currentText()):
        #    text+=f'_Channel{"_".join([str(chan.split("Channel ")[-1]) for chan in str(self.ccb_channels.currentText()).split(", ")])}'
        if self.le_condition.text():
            text+=f'_Condition_{str(self.le_condition.text())}'
        self.le_outputname.setText(text)
    
    def create_filter_window(self):
        if self.activefilter:
            self.activefilter=False
            self.filterwindow.close()
            return
        self.filterwindow
    
    def ErrorMsg(self, text, subtext=""):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(text)
        msg.setInformativeText(subtext)
        msg.setWindowTitle("Error")
        msg.exec_()
    def WarningMsg(self, text, subtext=""):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.setInformativeText(subtext)
        msg.setWindowTitle("Warning")
        msg.exec_()
    def WarningContinue(self, text, subtext):
        msg=QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.setInformativeText(subtext)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setWindowTitle("Warning")
        reply=msg.exec_()
        return reply
    def InfoMsg(self, text, subtext=""):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.setInformativeText(subtext)
        msg.setWindowTitle("Information")
        msg.exec_()
        
    def closeEvent(self, event):
        plt.close("all")
        event.accept()

def start():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    ui = Main(RunSortingfnc=GUIFunctions.RunSorting, SavePlotsfnc=GUIFunctions.SavePlots,
              ViewWholefnc=GUIFunctions.ViewWhole, ThrChangefnc=GUIFunctions.ThresholdChange,
              CutoffChangefnc=GUIFunctions.CutoffChange, IntervalChangefnc=GUIFunctions.IntervalChange,
              GetTimeStampsfnc=GUIFunctions.gettimestamps, UpdateWholePlotfnc=GUIFunctions.UpdateWholePlot)
    ui.show()
    sys.exit(app.exec())
        
    