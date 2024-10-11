# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 10:52:33 2024

@author: LukSu
"""
def toggleedit(parent, state):
    parent.comb_file.setDisabled(state)
    parent.ccb_channels.setDisabled(state)
    parent.le_condition.setReadOnly(state)
    parent.le_outputname.setReadOnly(state)
    parent.sb_refractair.setDisabled(state)
    parent.le_thresholds.setReadOnly(state)
    parent.cb_cutoff.setDisabled(state)
    parent.sb_cutoff.setDisabled(state)
    parent.le_timeinterval.setReadOnly(state)
    

def RunBatch(self, parent):
    #To prevent self.checks from raising a warning if thresholds in main window is left empty
    if self.le_thresholds[0].text()[0]=="[" and self.le_thresholds[0].text()[-1]=="]":
        thtext=self.le_thresholds[0].text()[1:-1].split(";")
    else:
        thtext=self.le_thresholds[0].text()
    parent.le_thresholds.setText(thtext[0])
    #check if everything needed is filled in
    channels=self.checks(parent)
    if not channels:
        return
    #Prevent the mainwindow variables from being edited
    toggleedit(parent, True)
    #Set all the mainwindow variables to the batch values
    baseout=str(parent.le_outputname.text())
    for ii in range(len(self.lbl_chtimeframes)):
        chtime=str(self.lbl_chtimeframes[ii].text()).split(": ")
        parent.ccb_channels.setCurrentText(chtime[0])
        string=f'{baseout}_ch{chtime[0].split(" ")[-1]}_time_{"_".join(chtime[1].split(" "))}'
        parent.le_outputname.setText(string)
        if self.le_thresholds[ii].text()[0]=="[" and self.le_thresholds[ii].text()[-1]=="]":
            thtext=self.le_thresholds[ii].text()[1:-1].split(";")
        else:
            thtext=self.le_thresholds[ii].text()
        #parent.le_thresholds.setText(self.le_thresholds[ii].text())
        parent.cb_cutoff.setChecked(self.cb_cutoffs[ii].isChecked())
        parent.sb_cutoff.setValue(self.sb_cutoffs[ii].value())
        parent.le_timeinterval.setText(chtime[1])
        for th in thtext:
            parent.le_thresholds.setText(th)
            parent.RunSorting(parent)
    toggleedit(parent, False)
        
def SaveBatch(self, parent):
    channels=self.checks(parent)
    if not channels:
        return
    toggleedit(parent, True)
    baseout=str(parent.le_outputname.text())
    for ii in range(len(self.lbl_chtimeframes)):
        chtime=str(self.lbl_chtimeframes[ii].text()).split(": ")
        parent.ccb_channels.setCurrentText(chtime[0])
        string=f'{baseout}_ch{chtime[0].split(" ")[-1]}_time_{"_".join(chtime[1].split(" "))}'
        parent.le_outputname.setText(string)
        parent.le_thresholds.setText(self.le_thresholds[ii].text())
        parent.cb_cutoff.setChecked(self.cb_cutoffs[ii].isChecked())
        parent.sb_cutoff.setValue(self.sb_cutoffs[ii].value())
        parent.le_timeinterval.setText(chtime[1])
        parent.SavePlots(parent)
    toggleedit(parent, False)
        