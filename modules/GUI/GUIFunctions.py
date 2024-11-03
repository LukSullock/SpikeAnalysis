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
import itertools
import re
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox
from modules.analysis.SpikeFunctions import (OpenRecording, DataSelect, SpikeSorting,
                                   SaveAll)
from modules.plot.plotfunctions import (PlotWholeRecording, PlotPartial,
                                   SpikeDetection, AverageWaveForm,
                                   InterSpikeInterval, AmplitudeDistribution)

class MplCanvas(FigureCanvas): #Custom canvas to be able to have in GUI plots
    def __init__(self, parent=None, width=5, height=4, dpi=100, size=1):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axs=[self.fig.add_subplot(size,1,1)]
        [self.axs.append(self.fig.add_subplot(size,1,ii+2,sharex=self.axs[0],sharey=self.axs[0])) for ii in range(size-1)]
        super(MplCanvas, self).__init__(self.fig)

class stdfigure(FigureCanvas): #Dummy class to be able to handle out of GUI plots the same as in GUI plots.
    pass

def CreateCanvas(pltsize, pltext=False):
    if pltext:
        canvas=stdfigure()
        canvas.fig, canvas.axs=plt.subplots(pltsize,sharex=True,sharey=True)
        if pltsize==1:
            canvas.axs=[canvas.axs]
        widget=None
    else:
        canvas = MplCanvas(width=5, height=4, dpi=100, size=pltsize)
        toolbar = NavigationToolbar(canvas)
        box=QVBoxLayout()
        box.addWidget(toolbar)
        box.addWidget(canvas)
        widget=QWidget()
        widget.setLayout(box)
    return widget, canvas

def addcanvas(self, widget, canvas, title, tab, file):
    self.canvassen.append([canvas, title, file])
    if widget:
        self.canvasboxes.append(widget)
        self.plt_container.addTab(self.canvasboxes[-1], tab)
        self.canvassen[-1][0].draw()
    else:
        canvas.fig.show()

def ViewWhole(self):
    file=str(self.comb_file.currentText())
    #if ".wav" not in str(self.comb_file.currentText()):
    #    return
    self.statusBar.showMessage('Importing')
    self.data,self.markers,self.time,self.framerate,nomarker=OpenRecording(f"{os.getcwd()}/data", str(self.comb_file.currentText()))
    if nomarker: self.WarningMsg("No marker file found.", """The marker file should be a txt file where the filename matches the filename of the audio file with -events after it.
For example:
    Audiofile: example.wav
    Markerfile: example-events.txt
Note that the extensions .wav and .txt are not always visible depending on your system settings. If you do not see them, you can ignore them.""")
    if self.cb_flipdata.isChecked():
        self.data=self.data*-1
    self.statusBar.showMessage('Creating Whole Recording Plot')
    if len(self.data)+1!=self.ccb_channels.count():
        for ii in reversed(range(self.ccb_channels.count())):
            if ii!=0:
                self.ccb_channels.removeItem(ii)
        self.ccb_channels.addItems([f"Channel {ii+1}" for ii in range(len(self.data))])
    self.lbl_markers.setText(f"Markers:\n{'\n'.join([f'{key}: {self.markers[key]}' for key in self.markers.keys()])}")
    channelc=self.ccb_channels.count()-1
    channels=[ii+1 for ii in range(channelc)]
    widget, canvas=CreateCanvas(len(self.data))
    canvas=PlotWholeRecording(canvas, self.data, self.markers, self.time, self.colorSTR, channels=channels, title=f"{file}: Whole")
    self.InfoMsg("Plot Created.", f"Filename {str(self.comb_file.currentText())}")
    self.canvassen.append([canvas, "Whole", file])
    self.canvasboxes.append(widget)
    self.plt_container.addTab(self.canvasboxes[-1], f"{file}: Whole recording (ch{channels})")
    self.canvassen[-1][0].draw()
    self.statusBar.showMessage('Finished')
    
def RunSorting(self):
    file=str(self.comb_file.currentText())
    if file=="Select file":
        self.ErrorMsg("Please select a datafile")
    #Check if plots need to be plotted in external windows or in GUI
    pltext=self.cb_externalplot.isChecked()
    if not "Select" in str(self.ccb_channels.currentText()):
        channels=[int(chan.split("Channel ")[-1]) for chan in str(self.ccb_channels.currentText()).split(", ")]
    else:
        self.ErrorMsg("Please select a channel.")
        return
    if len(str(self.le_thresholds.text()))==0:
        reply=self.WarningContinue("No thresholds set. Do you wish to continue?", "Warning, this will likely take a while to process.")
        if reply==QMessageBox.No: return
    maxprog=3
    currprog=0
    if self.cb_rawrecording.isChecked(): maxprog+=1
    if self.cb_selectedframes.isChecked(): maxprog+=1
    if self.cb_spikesorting.isChecked(): maxprog+=1
    if self.cb_averagewaveform.isChecked(): maxprog+=1
    if self.cb_interspikeinterval.isChecked(): maxprog+=1
    if self.cb_amplitudedistribution.isChecked(): maxprog+=1
    self.progressBar.setValue(0)
    self.statusBar.showMessage('Running')
    self.data,self.markers,self.time,self.framerate,nomarker=OpenRecording(f"{os.getcwd()}/data", str(self.comb_file.currentText()))
    if self.cb_flipdata.isChecked():
        self.data=self.data*-1
    currprog+=1
    self.progressBar.setValue(int(currprog/maxprog*100))
    if nomarker: self.WarningMsg("No marker file found.", """The marker file should be a txt file where the filename matches the filename of the audio file with -events after it.
For example:
    Audiofile: example.wav
    Markerfile: example-events.txt
Note that the extensions .wav and .txt are not always visible depending on your system settings. If you do not see them, you can ignore them.""")
    #Only keep data for selected channels    
    datasel=[self.data[chan-1] for chan in channels]
    #Apply filters if applicable
    #######
    
    
    #Run all checked options, and necessary functions for variables
    #If cutoff has been selected, take value, otherwise set to false
    if self.cb_cutoff.isChecked():
        self.cutoff_thresh=[self.sb_cutoff.value()]
    else:
        self.cutoff_thresh=[] #functions need the variable assigned to either False or a number to be able to function
    #Raw recording
    if self.cb_rawrecording.isChecked():
        self.statusBar.showMessage('Raw Recording')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=PlotWholeRecording(canvas, datasel, {}, self.time, self.colorSTR, channels=channels, title=f"{file}: Raw")
        addcanvas(self, widget, canvas, "Raw", f"{file}: Raw recording (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    self.statusBar.showMessage('Data Selection')
    self.xlim,self.DataSelection=DataSelect(datasel, self.markers, self.framerate, str(self.le_timeinterval.text()))
    if not self.xlim: self.ErrorMsg("Error in Time intervals.",f"Marker {self.DataSelection[0]}\n{self.DataSelection[1]}"); return
    currprog+=1
    self.progressBar.setValue(int(currprog/maxprog*100))
    #Plot selected time frame
    if self.cb_selectedframes.isChecked():
        self.statusBar.showMessage('Partial Recording')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=PlotPartial(canvas, self.markers, self.DataSelection, self.time,self.xlim, self.colorSTR, self.cutoff_thresh, str(self.le_thresholds.text()), channels=channels, title=f"{file}: Partial")
        addcanvas(self, widget, canvas, "Partial", f"{file}: Partial recording (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    #Spike sorting
    self.statusBar.showMessage('Spike Sorting')
    self.clusters=SpikeSorting(self.DataSelection, str(self.le_thresholds.text()), self.sb_refractair.value(), self.framerate, self.time, self.cutoff_thresh)
    currprog+=1
    self.progressBar.setValue(int(currprog/maxprog*100))
    #Plot spike sorting
    if self.cb_spikesorting.isChecked():
        self.statusBar.showMessage('Spike Detection')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=SpikeDetection(canvas, self.clusters, self.time, self.DataSelection, self.xlim, self.colorSTR, self.cutoff_thresh, channels=channels, title=f"{file}: Spike")
        addcanvas(self, widget, canvas, "Spike", f"{file}: Spike sorting (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_averagewaveform.isChecked():
        self.statusBar.showMessage('Average Waveform')
        widgets=[]
        canvasses=[]
        for ii, chan in enumerate(self.clusters):
            for cl in chan:
                widget, canvas=CreateCanvas(1, pltext)
                widgets.append(widget)
                canvasses.append(canvas)
        canvasses, clus=AverageWaveForm(canvasses, self.framerate, self.clusters, self.DataSelection, channels=channels, title=f"{file}: Average")
        for ii, canvas in enumerate(canvasses):
            addcanvas(self, widgets[ii], canvas, "AWave", f"{file}: {clus[ii]}", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_interspikeinterval.isChecked():
        self.statusBar.showMessage('Inter Spike Interval')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=InterSpikeInterval(canvas, self.clusters,self.framerate,self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "ISI", f"{file}: Interspike interval (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_amplitudedistribution.isChecked():
        self.statusBar.showMessage('Amplitude Distribution')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=AmplitudeDistribution(canvas, self.clusters,self.framerate,self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "AmpDis", f"{file}: Amplitude distribution (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    self.progressBar.setValue(100)
    self.statusBar.showMessage('Finished')
    
def ThresholdChange(self):
    #Remove old thresholds
    ncnvs=-1
    for ii in reversed(range(len((self.canvassen)))):
        if "Whole" in self.canvassen[ii][1]:
            ncnvs=ii
            break
    if ncnvs==-1: return
    colorcycle=itertools.cycle(self.colorSTR)
    for line in self.threshlines:
        line.remove()
    self.threshlines=[]
    self.canvassen[ncnvs][0].draw_idle()
    thresstr=str(self.le_thresholds.text())
    if len(thresstr)==0: return #return if no threshold is given
    if not self.canvassen: return #return if there is no canvas
    thresholdstmpstr=[th for th in re.split(r"\b\D+", thresstr)] #regular expression to filter out all numbers and convert each to int
    thresholdstmp=[]
    error=False
    for th in thresholdstmpstr:
        try:
            thresholdstmp.append(int(th))
        except ValueError as err:
            if th:
                error=[f"Marker {str(err)}", traceback.format_exc()]
            continue
    thresholds=list(set(thresholdstmp))
    for thr in thresholds:
        color=next(colorcycle)
        for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
            self.threshlines.append(self.canvassen[ncnvs][0].axs[ii].axhline(thr, color=color))
    self.canvassen[ncnvs][0].draw_idle()
    if error: self.WarningMsg("Not all thresholds were convertable to integers.",f"Marker {error[0]}\n{error[1]}")

def CutoffChange(self):
    #Remove old cut off threshold
    ncnvs=-1
    for ii in reversed(range(len((self.canvassen)))):
        if "Whole" in self.canvassen[ii][1]:
            ncnvs=ii
            break
    if ncnvs==-1: return
    for rec in self.cutoffrec:
        rec.remove()
    self.cutoffrec=[]
    cutoffthresh=int(self.sb_cutoff.text())
    self.canvassen[ncnvs][0].draw_idle()
    if not self.cb_cutoff.isChecked() or not cutoffthresh or not self.canvassen: return
    for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
        ylim=self.canvassen[ncnvs][0].axs[ii].get_ylim()
        xlim=self.canvassen[ncnvs][0].axs[ii].get_xlim()
        self.cutoffrec.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
            (0,cutoffthresh), xlim[1], ylim[1]-cutoffthresh, color=(1,0,0,0.3))))
    self.canvassen[ncnvs][0].draw_idle()
    
def IntervalChange(self):
    #Remove old cut off threshold
    ncnvs=-1
    for ii in reversed(range(len((self.canvassen)))):
        if "Whole" in self.canvassen[ii][1]:
            ncnvs=ii
            break
    for interval in self.intervals:
        interval.remove()
    self.intervals=[]
    if ncnvs==-1: return
    times=str(self.le_timeinterval.text())
    times=times.split(" and ")
    for ii,art in enumerate(times):
        times[ii]=art.split(" to ")
    self.canvassen[ncnvs][0].draw_idle()
    if not all([all(interval) for interval in times]) or any([len(interval)<2 for interval in times]) or not self.canvassen: return
    for ii,th in enumerate(times):
        for jj,art in enumerate(th):
            #If marker then use maker time, otherwise convert string to float
            if "m" in art or "M" in art:
                if len(art)==1: return
                try:
                    times[ii][jj]=self.markers[int(times[ii][jj][-1])][0]
                except (IndexError, ValueError):
                    return
            else:
                try:
                    times[ii][jj]=float(times[ii][jj])
                except ValueError:
                    return
    start_time=[art[0] for art in times]
    stop_time=[art[1] for art in times]
    if not start_time: return
    for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
        ylim=self.canvassen[ncnvs][0].axs[ii].get_ylim()
        xlim=self.canvassen[ncnvs][0].axs[ii].get_xlim()
        self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
            (0,ylim[0]), start_time[0], abs(ylim[0])+abs(ylim[1]), color=(1,0,0,0.3))))
        for jj,start in enumerate(start_time):
            if jj==0: continue
            self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
                (stop_time[jj-1],ylim[0]), start-stop_time[jj-1], abs(ylim[0])+abs(ylim[1]), color=(1,0,0,0.3))))
        self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
            (stop_time[-1],ylim[0]), xlim[1]-stop_time[-1], abs(ylim[0])+abs(ylim[1]), color=(1,0,0,0.3))))
    self.canvassen[ncnvs][0].draw_idle()

def UpdateWholePlot(self):
    ThresholdChange(self)
    CutoffChange(self)
    IntervalChange(self)

def SavePlots(self):
    #Get data, save everything, then close all plots
    self.closePlots()
    self.cb_externalplot.setChecked(True)
    ViewWhole(self)
    ThresholdChange(self)
    CutoffChange(self)
    IntervalChange(self)
    self.RunSorting(self)
    SaveAll(self.clusters, self.xlim[0], self.xlim[1], f"{os.getcwd()}/saved", str(self.le_outputname.text()),self.cutoff_thresh)
    #plt.close('all')

def gettimestamps(self, times):
    for ii,th in enumerate(times):
        for jj,art in enumerate(th):
            #If marker then use maker time, otherwise convert string to float
            if "m" in art or "M" in art:
                if len(art)==1: return
                try:
                    times[ii][jj]=self.markers[int(times[ii][jj][-1])][0]
                except IndexError as err:
                    self.ErrorMsg("Error in time intervals",f"Marker {str(err)}\n{traceback.format_exc()}")
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
                except ValueError as err:
                    self.ErrorMsg("Error in time intervals",f"Marker {str(err)}\n{traceback.format_exc()}")
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
            else:
                try:
                    times[ii][jj]=float(times[ii][jj])
                except ValueError as err:
                    self.ErrorMsg("Error in time intervals",f"Marker {str(err)}\n{traceback.format_exc()}")
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
    start_time=[art[0] for art in times]
    stop_time=[art[1] for art in times]
    return start_time, stop_time