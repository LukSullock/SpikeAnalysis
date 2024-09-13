# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 20:31:28 2024

@author: LukSu
"""
import os
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
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

class stdfigure(object): #Dummy class to be able to handle out of GUI plots the same as in GUI plots.
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

def ViewRaw(self):
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
    self.canvassen.append([canvas, "Raw"])
    if not self.cb_externalplot.isChecked():
        self.canvasboxes.append(widget)
        self.plt_container.addTab(self.canvasboxes[-1], f"Raw recording (ch{channels})")
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
    #Whole recording
    if self.cb_wholerecording.isChecked():
        widget, canvas=CreateCanvas(len(self.data),pltext)
        canvas=PlotWholeRecording(canvas, datasel, self.markers, self.time, self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "Whole", f"Whole recording (ch{channels})")
    self.xlim,self.DataSelection=DataSelect(datasel, self.markers, self.framerate, str(self.le_timeinterval.text()))
    if not self.xlim: self.ErrorMsg(self.DataSelection[0],self.DataSelection[1]); return
    #Plot selected time frame
    if self.cb_selectedframes.isChecked():
        widget, canvas=CreateCanvas(len(self.data),pltext)
        canvas=PlotPartial(canvas, self.markers, self.DataSelection, self.time,self.xlim, self.colorSTR, channels=channels)
        addcanvas(self, widget, canvas, "Partial", f"Partial recording (ch{channels})")
    #Spike sorting
    self.clusters=SpikeSorting(self.DataSelection, str(self.le_thresholds.text()), self.sb_refractair.value(), self.framerate, self.time, self.cutoff_thresh)
    #Plot spike sorting
    if self.cb_spikesorting.isChecked():
        widget, canvas=CreateCanvas(len(self.data),pltext)
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
        widget, canvas=CreateCanvas(len(self.data),pltext)
        canvas=InterSpikeInterval(canvas, self.clusters,self.framerate,self.colorSTR)
        addcanvas(self, widget, canvas, "ISI", f"Interspike interval (ch{channels})")
    if self.cb_amplitudedistribution.isChecked():
        widget, canvas=CreateCanvas(len(self.data),pltext)
        canvas=AmplitudeDistribution(canvas, self.clusters,self.framerate,self.colorSTR)
        addcanvas(self, widget, canvas, "AmpDis", f"Amplitude distribution (ch{channels})")

def SavePlots(self):
    #Get data, save everything, then close all plots
    self.RunSorting()
    SaveAll(self.clusters, self.xlim, f"{os.getcwd()}/saved", [int(chan.split("Channel ")[-1]) for chan in str(self.ccb_channels.currentText()).split(", ")], str(self.le_outputname.text()),self.cutoff_thresh)
    #plt.close('all')
