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
import numpy as np
from PyQt5 import QtCore
from decimal import Decimal, ROUND_HALF_UP
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox, QInputDialog
from modules.analysis.SpikeFunctions import (OpenRecording, DataSelect, SpikeSorting,
                                   SaveAll)
from modules.plot.PlotFunctions import (PlotWholeRecording, PlotPartial,
                                   SpikeDetection, AverageWaveForm,
                                   InterSpikeInterval, AmplitudeDistribution,
                                   ERPplots, Spectrogram, AutoCorrelation,
                                   CrossCorrelation)
from modules.GUI.Ui_SpikeSorting import crosscorrDialog

class MplCanvas(FigureCanvas):
    """Class so that Matplotlib figures can displayed in the GUI"""
    def __init__(self, parent=None, width=5, height=4, dpi=100, size=1):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axs=[self.fig.add_subplot(size,1,1)]
        [self.axs.append(self.fig.add_subplot(size,1,ii+2,sharex=self.axs[0],sharey=self.axs[0])) for ii in range(size-1)]
        super(MplCanvas, self).__init__(self.fig)

class stdfigure(FigureCanvas):
    """Dummy class to be able to handle out of GUI plots the same as in GUI plots."""
    pass

def CreateCanvas(pltsize, pltext=False):
    """
    Function to create a canvas in which the Matplotlib plot will be plotted.

    Parameters
    ----------
    pltsize : int
        How many subplots there should be.
    pltext : bool, optional
        Defines if the plot will be plotted externally or internaly in the GUI. The default is False.

    Returns
    -------
    widget : QWidget
        Widget containing the canvas.
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
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
    """
    Function to add a widget containing a canvas to the GUI

    Parameters
    ----------
    widget : QWidget
        Widget containing the canvas.
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    title : string
        Short description of the plot type.
    tab : string
        Name of the tab.
    file : string
        Name of the origin file of the data.

    """
    self.canvassen.append([canvas, title, file])
    if widget:
        self.canvasboxes.append(widget)
        self.plt_container.addTab(self.canvasboxes[-1], tab)
        self.canvassen[-1][0].draw()
    else:
        canvas.fig.show()

def FindMarkers(markerdata, markers, framerate):
    """
    Function to extract markers from an EEG marker channel
    
    NOTE: The channel needs to be noise free

    Parameters
    ----------
    markerdata : list
        List containing the data points of the marker channel.
    markers : defaultdict
        Defaultdict containing marker times per marker.
    framerate : int
        Framerate of the markerdata.

    Returns
    -------
    markers : defaultdict
        Defaultdict containing marker times per marker.

    """
    startsearch=True
    for ii, value in enumerate(markerdata):
        if startsearch and value!=0:
            markers[str(value)].append(ii/framerate)
            startsearch=False
        elif value==0:
            startsearch=True
    return markers

def ViewWhole(self):
    """
    Function to create and add a canvas of the whole recording to the GUI.
    The whole recording is meant to display all the data and the time frames, thresholds, and cut-off threshold.
    
    NOTE: The whole recording plot will always be displayed in the GUI and can therefor not be automatically saved.

    """
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
    if ".mat" in str(self.comb_file.currentText()):
        self.framerate, _=QInputDialog.getInt(self,"Framerate","Enter the framerate (Hz) of the recording:", 500, 1)
        markerchannel, _=QInputDialog.getInt(self,"Marker channel","Enter the channel used for markers. If there is none, fill in 0:", 0, 0, len(self.data))
        if markerchannel:
            markerdata=self.data[markerchannel-1]
            self.data=np.delete(self.data, markerchannel-1, axis=0)
            self.markers=FindMarkers(markerdata, self.markers, self.framerate)
        self.time=np.array([x/self.framerate for x in np.arange(np.size(self.data, 1))]) # in seconds
    self.data=self.filter_data(self.data, self.framerate, low=self.lowpass, high=self.highpass, notch=self.notchv, order=2, notchfilter=self.notchfilter, bandfilter=self.bandfilter)
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
    for ii,ch in enumerate(self.data):
        m = ch.mean(0)
        sd = ch.std(axis=0, ddof=0)
        SNR=abs(np.where(sd == 0, 0, m/sd))
        SNRtxt=Decimal(str(SNR))
        SNRtxt=SNRtxt.quantize(Decimal('0.0001'), ROUND_HALF_UP) #Proper rounding
        xlim=max(canvas.axs[ii].get_xlim())
        ylim=max(canvas.axs[ii].get_ylim())
        canvas.axs[ii].text(0.9*xlim,0.9*ylim,f'SNR: {SNRtxt}')
    self.InfoMsg("Plot Created.", f"Filename {str(self.comb_file.currentText())}")
    self.canvassen.append([canvas, "Whole", file])
    self.canvasboxes.append(widget)
    self.plt_container.addTab(self.canvasboxes[-1], f"{file}: Whole recording (ch{channels})")
    self.canvassen[-1][0].draw()
    self.statusBar.showMessage('Finished')
    
def RunSorting(self, spikesort=False):
    """
    Function to run the analysis. Creates all selected plots and data required.

    Parameters
    ----------
    spikesort : bool, optional
        Determines if the SpikeSorting function should be ran (see SpikeFunctions.py).
        Will be set to True automatically if it is needed. The default is False.

    """
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
    maxprog=2
    currprog=0
    if self.cb_rawrecording.isChecked(): maxprog+=1
    if self.cb_selectedframes.isChecked(): maxprog+=1
    if self.cb_spikesorting.isChecked(): maxprog+=1; spikesort=True
    if self.cb_averagewaveform.isChecked(): maxprog+=1; spikesort=True
    if self.cb_interspikeinterval.isChecked(): maxprog+=1; spikesort=True
    if self.cb_amplitudedistribution.isChecked(): maxprog+=1; spikesort=True
    if self.cb_autocorr.isChecked(): maxprog+=1; spikesort=True
    if self.cb_crosscorr.isChecked(): maxprog+=1; spikesort=True
    if self.cb_powerfreq.isChecked(): maxprog+=1
    if self.cb_erp.isChecked(): maxprog+=1
    if spikesort: maxprog+=1
    
    if len(str(self.le_thresholds.text()))==0 and spikesort:
        reply=self.WarningContinue("No thresholds set. Do you wish to continue?", "Warning, this will likely take a while to process.")
        if reply==QMessageBox.No: return
    self.progressBar.setValue(0)
    self.statusBar.showMessage('Running')
    self.data,self.markers,self.time,self.framerate,nomarker=OpenRecording(f"{os.getcwd()}/data", str(self.comb_file.currentText()))
    if ".mat" in str(self.comb_file.currentText()):
        self.framerate, _=QInputDialog.getInt(self,"Framerate","Enter the framerate (Hz) of the recording:", 500, 1)
        markerchannel, _=QInputDialog.getInt(self,"Marker channel","Enter the channel used for markers. If there is none, fill in 0:", 0, 0, len(self.data))
        if markerchannel:
            markerdata=self.data[markerchannel-1]
            self.data=np.delete(self.data, markerchannel-1, axis=0)
            self.markers=FindMarkers(markerdata, self.markers, self.framerate)
        self.time=np.array([x/self.framerate for x in np.arange(np.size(self.data, 1))]) # in seconds
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
    datasel=self.filter_data(datasel, self.framerate, low=self.lowpass, high=self.highpass, notch=self.notchv, order=2, notchfilter=self.notchfilter, bandfilter=self.bandfilter)
    
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
    self.xlim,self.DataSelection, self.markers=DataSelect(datasel, self.markers, self.framerate, str(self.le_timeinterval.text()))
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
    if spikesort:
        self.statusBar.showMessage('Spike Sorting')
        self.clusters=SpikeSorting(self.DataSelection, str(self.le_thresholds.text()), self.sb_refractair.value(), self.framerate, self.time, self.cutoff_thresh)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    else: self.clusters=[]
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
        canvasses, clus=AverageWaveForm(canvasses, self.clusters, self.framerate, self.DataSelection, channels=channels, title=f"{file}: Average")
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
    if self.cb_autocorr.isChecked():
        self.statusBar.showMessage('Autocorrelogram')
        widgets=[]
        canvasses=[]
        for ii, chan in enumerate(self.clusters):
            for cl in chan:
                widget, canvas=CreateCanvas(1, pltext)
                widgets.append(widget)
                canvasses.append(canvas)
        canvasses, clus=AutoCorrelation(canvasses, self.clusters, self.framerate, self.colorSTR, intervalsize=2, channels=channels)
        for ii, canvas in enumerate(canvasses):
            addcanvas(self, widgets[ii], canvas, "Autocorr", f"{file}: Autocorrelogram {clus[ii]}", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_crosscorr.isChecked():
        self.statusBar.showMessage('Crosscorrelogram')
        #Show plots so that previous plots can be used in determining which clusters are to be cross correlated
        plt.show()
        self.x1=[0,0] #[channel, cluster]
        self.x2=[0,1]
        #Custom input dialog for selecting clusters
        ccdia=crosscorrDialog(self)
        ccdia.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        ccdia.show()
        #Event loop to pause main window
        loop = QtCore.QEventLoop()
        #Exit event loop when the input dialog is closed
        ccdia.destroyed.connect(loop.quit)
        #Execute event loop
        loop.exec()
        widget, canvas=CreateCanvas(1,pltext)
        #Window to ask for which clusters to compare; likely in format of drop down boxes or int invul
        x1=self.x1
        x2=self.x2
        canvas, tabtitle=CrossCorrelation(canvas, self.clusters, self.framerate, self.colorSTR, intervalsize=2, x1=x1, x2=x2)
        #Edit tab title to include cluster threshold instead of index
        addcanvas(self, widget, canvas, "Crosscorr", f"{file}: {tabtitle}", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_powerfreq.isChecked():
        self.statusBar.showMessage('Powerfrequentie plot')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas=Spectrogram(canvas, self.DataSelection, self.framerate, self.time, channels=channels)
        addcanvas(self, widget, canvas, "Spectro", f"{file}: Spectrogram (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    if self.cb_erp.isChecked():
        self.statusBar.showMessage('ERP plot')
        widget, canvas=CreateCanvas(len(datasel),pltext)
        canvas, self.erpsignal=ERPplots(canvas, self.DataSelection, self.markers, self.framerate, self.colorSTR, xmin=self.sb_erpmin.value(), xmax=self.sb_erpmax.value(), channels=channels)
        addcanvas(self, widget, canvas, "ERP", f"{file}: Event-Related Potential (ch{channels})", file)
        currprog+=1
        self.progressBar.setValue(int(currprog/maxprog*100))
    self.progressBar.setValue(100)
    self.statusBar.showMessage('Finished')

def GetTab(self):
    """
    Function to get the tab index of the whole recording of the selected the file.

    Returns
    -------
    indx : int
        Index of the whole recording tab that corresponds to the selected file.

    """
    text=str(self.comb_file.currentText())
    for indx, canvas in enumerate(self.canvassen):
        if self.plt_container.tabText(indx).split(":")[0]==text:
            return indx
    for indx in reversed(range(len((self.canvassen)))):
        if "Whole" in self.canvassen[indx][1]:
            return indx
    return -1
    
def ThresholdChange(self):
    """Function to remove old thresholds and add the filled in threshold(s) to the whole recording plot."""
    #Remove old thresholds
    ncnvs=GetTab(self)
    if ncnvs==-1: return
    colorcycle=itertools.cycle(self.colorSTR)
    for line in self.threshlines:
        line.remove()
    self.threshlines=[]
    self.canvassen[ncnvs][0].draw_idle()
    thresstr=str(self.le_thresholds.text())
    if len(thresstr)==0: return #return if no threshold is given
    if not self.canvassen: return #return if there is no canvas
    thresholdstmpstr=[th for th in re.split(r"\b\D+", thresstr) if th] #regular expression to filter out all numbers and convert each to int
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
    """Function to remove the old cut-off threshold and add the filled in cut-off threshold to the whole recording plot."""
    #Remove old cut off threshold
    ncnvs=GetTab(self)
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
    """Function to remove the old time intervals and add the filled in time intervals to the whole recording plot."""
    #Remove old cut off threshold
    ncnvs=GetTab(self)
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
    """Function to update time intervals, threshold, and cut-off threshold in the whole recording plot."""
    ThresholdChange(self)
    CutoffChange(self)
    IntervalChange(self)

def SavePlots(self):
    """
    Function to run the RunSorting function, see modules/GUI/GUIFunctions. Data is saved to the /saved directory.
    
    NOTE: The whole recording plot needs to be manually saved by pressing the save button in the top left of the plot.

    """
    #Close all plots
    self.closePlots()
    #Set external plots to True, otherwise they cannot be saved
    self.cb_externalplot.setChecked(True)
    #Add a whole recording plot and update it with the time intervals, thresholds, and cut-off threshold
    ViewWhole(self)
    ThresholdChange(self)
    CutoffChange(self)
    IntervalChange(self)
    #Run the sorting function
    self.RunSorting(self)
    #Get the channels, then save everything to files in the /saved directory.
    channels=[int(chan.split("Channel ")[-1]) for chan in str(self.ccb_channels.currentText()).split(", ")]
    output=str(self.le_outputname.text())
    folder=f"{os.getcwd()}/saved"
    cancelsave=False
    #While loop to catch unintended overwriting of files
    fileoverwrite=True
    while fileoverwrite:
        fileoverwrite=False
        for jj,chan in enumerate(self.clusters):
            for ii,cl in enumerate(chan):
                path=os.path.join(folder,f'spiketimes_{output}_channel{channels[jj]}_cluster{ii+1}.csv')
                if os.path.isfile(path):
                    fileoverwrite=True
        path=os.path.join(folder,f"Plots_{output}.pdf")
        if os.path.isfile(path):
            fileoverwrite=True
        if self.erpsignals:
            for ii,ch in enumerate(self.erpsignals):
                path=os.path.join(folder,f'ERP_{output}_channel{channels[ii]}.csv')
                if os.path.isfile(path):
                    fileoverwrite=True
        if fileoverwrite:
            output, ok=QInputDialog.getText(self, f'File with output output: "{output}" already exists',
                                            "Enter new output name or press cancel to cancel running.\nLeave the output the same to overwrite.", f'{output}')
            fileoverwrite=False
            if not ok:
                cancelsave=True
    if cancelsave: return
    SaveAll(self.clusters, self.erpsignal, self.xlim[0], self.xlim[1], folder, output,self.cutoff_thresh, channels)
    self.InfoMsg(f'Files for {str(self.le_outputname.text())} {channels} saved.', f'Files can be found at {os.getcwd()}/saved')

def gettimestamps(self, times):
    """
    Function to convert markers to its timestamps.
    
    NOTE: will always take the first timestamp of a marker if it has multiple. 

    Parameters
    ----------
    times : list
        List containing the strings per time interval.

    Returns
    -------
    start_time : list
        List of all the start times of the chosen time frames.
    stop_time : list
        List of all the stop times of the chosen time frames.

    """
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
