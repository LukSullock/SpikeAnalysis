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
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from modules.analysis.SpikeSorting import (OpenRecording, DataSelect, SpikeSorting,
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

def ViewWhole(self):
    if ".wav" not in str(self.comb_file.currentText()):
        return
    self.data,self.markers,self.time,self.framerate=OpenRecording(f"{os.getcwd()}/data", str(self.comb_file.currentText()))
    if len(self.data)+1!=self.ccb_channels.count():
        for ii in reversed(range(self.ccb_channels.count())):
            if ii!=0:
                self.ccb_channels.removeItem(ii)
        self.ccb_channels.addItems([f"Channel {ii+1}" for ii in range(len(self.data))])
    self.lbl_markers.setText(f"Markers:\n{'\n'.join([f'{key}: {self.markers[key]}' for key in self.markers.keys()])}")
    channelc=self.ccb_channels.count()-1
    channels=[ii+1 for ii in range(channelc)]
    inplot=self.cb_externalplot.isChecked()
    widget, canvas=CreateCanvas(len(self.data), inplot)
    canvas=PlotWholeRecording(canvas, self.data, self.markers, self.time, self.colorSTR, channels=channels)
    self.canvassen.append([canvas, "Whole"])
    if not self.cb_externalplot.isChecked():
        self.canvasboxes.append(widget)
        self.plt_container.addTab(self.canvasboxes[-1], f"Whole recording (ch{channels})")
        self.canvassen[-1][0].draw()

def addcanvas(self, widget, canvas, title, tab):
    self.canvassen.append([canvas, title])
    if widget:
        self.canvasboxes.append(widget)
        self.plt_container.addTab(self.canvasboxes[-1], tab)
        self.canvassen[-1][0].draw()
    else:
        canvas.fig.show()

def RunSorting(self):
    #Run all checked options, and necessary functions for variables
    #Check if plots need to be plotted in external windows or in GUI
    pltext=self.cb_externalplot.isChecked()
    if not "Select" in str(self.ccb_channels.currentText()):
        channels=[int(chan.split("Channel ")[-1]) for chan in str(self.ccb_channels.currentText()).split(", ")]
    else:
        return
    self.data,self.markers,self.time,self.framerate=OpenRecording(f"{os.getcwd()}/data", str(self.comb_file.currentText()))
    datasel=[self.data[chan-1] for chan in channels]
    #Apply filters if applicable
    #######
    
    
    #If cutoff has been selected, take value, otherwise set to false
    if self.cb_cutoff.isChecked():
        self.cutoff_thresh=int(self.sb_cutoff.text())
    else:
        self.cutoff_thresh=False #functions need the variable assigned to either False or a number to be able to function
    #Raw recording
    if self.cb_rawrecording.isChecked():
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=PlotWholeRecording(canvas, datasel, {}, self.time, self.colorSTR, channels=channels, title="Raw")
        addcanvas(self, widget, canvas, "Raw", f"Raw recording (ch{channels})")
    self.xlim,self.DataSelection=DataSelect(datasel, self.markers, self.framerate, str(self.le_timeinterval.text()))
    if not self.xlim: self.ErrorMsg(self.DataSelection[0],self.DataSelection[1]); return
    #Plot selected time frame
    if self.cb_selectedframes.isChecked():
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=PlotPartial(canvas, self.markers, self.DataSelection, self.time,self.xlim, self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "Partial", f"Partial recording (ch{channels})")
    #Spike sorting
    self.clusters=SpikeSorting(self.DataSelection, str(self.le_thresholds.text()), self.sb_refractair.value(), self.framerate, self.time, self.cutoff_thresh)
    #Plot spike sorting
    if self.cb_spikesorting.isChecked():
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=SpikeDetection(canvas, self.clusters, self.time, self.DataSelection, self.xlim,self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "Spike", f"Spike sorting (ch{channels})")
    if self.cb_averagewaveform.isChecked():
        widgets=[]
        canvasses=[]
        for ii, chan in enumerate(self.clusters):
            for cl in chan:
                widget, canvas=CreateCanvas(1, pltext)
                widgets.append(widget)
                canvasses.append(canvas)
        canvasses, clus=AverageWaveForm(canvasses, self.framerate, self.clusters, self.DataSelection, channels=channels)
        for ii, canvas in enumerate(canvasses):
            addcanvas(self, widgets[ii], canvas, "AWave", clus[ii])
    if self.cb_interspikeinterval.isChecked():
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=InterSpikeInterval(canvas, self.clusters,self.framerate,self.colorSTR)
        addcanvas(self, widget, canvas, "ISI", f"Interspike interval (ch{channels})")
    if self.cb_amplitudedistribution.isChecked():
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=AmplitudeDistribution(canvas, self.clusters,self.framerate,self.colorSTR)
        addcanvas(self, widget, canvas, "AmpDis", f"Amplitude distribution (ch{channels})")

def ThresholdChange(self):
    #Remove old thresholds
    ncnvs=-1
    for ii,canvas in enumerate(self.canvassen):
        if "Whole" in canvas[1]:
            ncnvs=ii
            break
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
    for th in thresholdstmpstr:
        try:
            thresholdstmp.append(int(th))
        except ValueError:
            continue
    thresholds=list(set(thresholdstmp))
    if ncnvs!=-1:
        for thr in thresholds:
            color=next(colorcycle)
            for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
                self.threshlines.append(self.canvassen[ncnvs][0].axs[ii].axhline(thr, color=color))
    self.canvassen[ncnvs][0].draw_idle()

def CutoffChange(self):
    #Remove old cut off threshold
    ncnvs=-1
    for ii,canvas in enumerate(self.canvassen):
        if "Whole" in canvas[1]:
            ncnvs=ii
            break
    for rec in self.cutoffrec:
        rec.remove()
    self.cutoffrec=[]
    cutoffthresh=int(self.sb_cutoff.text())
    self.canvassen[ncnvs][0].draw_idle()
    if not self.cb_cutoff.isChecked() or not cutoffthresh or not self.canvassen: return
    if ncnvs!=-1:
        for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
            ylim=self.canvassen[ncnvs][0].axs[ii].get_ylim()
            xlim=self.canvassen[ncnvs][0].axs[ii].get_xlim()
            self.cutoffrec.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
                (0,cutoffthresh), xlim[1], ylim[1]-cutoffthresh, color=(1,0,0,0.3))))
    self.canvassen[ncnvs][0].draw_idle()
    

def IntervalChange(self):
    #Remove old cut off threshold
    ncnvs=-1
    for ii,canvas in enumerate(self.canvassen):
        if "Whole" in canvas[1]:
            ncnvs=ii
            break
    for inter in self.intervals:
        inter.remove()
    self.intervals=[]
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
                try:
                    times[ii][jj]=self.markers[int(times[ii][jj][-1])][0]
                except IndexError as err:
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
                except ValueError as err:
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
            else:
                try:
                    times[ii][jj]=float(times[ii][jj])
                except ValueError as err:
                    return False, [f"Marker {str(err)}", traceback.format_exc()]
    
    start_time=[art[0] for art in times]
    stop_time=[art[1] for art in times]
    if ncnvs!=-1:
        for ii,axs in enumerate(self.canvassen[ncnvs][0].axs):
            ylim=self.canvassen[ncnvs][0].axs[ii].get_ylim()
            xlim=self.canvassen[ncnvs][0].axs[ii].get_xlim()
            self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
                (0,ylim[0]), start_time[0], 2*ylim[1], color=(1,0,0,0.3))))
            for jj,start in enumerate(start_time):
                if jj==0: continue
                self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
                    (stop_time[jj-1],ylim[0]), start-stop_time[jj-1], 2*ylim[1], color=(1,0,0,0.3))))
            self.intervals.append(self.canvassen[ncnvs][0].axs[ii].add_patch(Rectangle(
                (stop_time[-1],ylim[0]), xlim[1]-stop_time[-1], 2*ylim[1], color=(1,0,0,0.3))))
    self.canvassen[ncnvs][0].draw_idle()
    
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
