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
import itertools
import math
import re
import numpy as np

def cross_correlation(spikeset1, spikeset2, interval):
    """
    Function to calculate cross correlation.
    Giving the same spikeset twice will calculate autocorrelation.

    Parameters
    ----------
    spikeset1 : list of int
        First set of spike timings in frames.
    spikeset2 : list of int
        Second set of spike timings in frames.
    interval : int
        Interval in frames to calculate cross correlation in.

    Returns
    -------
    cross : numpy.array
        Array containing the amount of spikes at a given relative datapoint.

    """
    cross = np.zeros(int(2*interval+1), 'd') #prepare array filled with zeros
    startint=0 #index at which spike search is started
    for spike in spikeset1:
        ii=startint
        #Look for the index of the first spike in spikeset2 that is within the interval
        while ii<len(spikeset2) and spikeset2[ii]-spike<-interval:
            ii+=1
        startint=ii #update startint to skip values that are certain to be outside the interval of the next spike
        #Add spikes to the correct bins
        while ii<len(spikeset2) and spikeset2[ii]-spike<=interval:
            cross[int(spikeset2[ii]-spike+interval)]+=1
            ii+=1
    return cross

def PlotDataFigure(canvas, data, time, xlabel="", ylabel="", color="k", *, legend=False, xlim=False, lw=1, curves=[], vlines=[],hlines=[], scatterpoints=[], colorcycle=itertools.cycle("rbymgc"), title="", text=[]):
    """
    Function to make a line plot or scatter plot.

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    data : Array of int64
        Array containing y-values per channel.
    time : Array of float64
        Array containing x-values per channel. First index is channel, second contains x-values.
    xlabel : String, optional
        Labelname for x-axis. The default is "".
    ylabel : String, optional
        Labelname for y-axis. The default is "".
    color : String, optional
        Matplotlib colour denotions. Defines the colour of the plotting for the data parameter. The default is "k" (black).
    legend : Bool, optional
        Denotes if a legend should be added. The default is False.
    xlim : list, optional
        List of a list of start times and a list of stop times for the time frames. x limit will be set from the first start value to the last stop value. The default is False.
    lw : Int, optional
        Linewidth. Defines the colour of the plotting for the data parameter. The default is 1.
    curves : list, optional
        list of a list of curves. List of a curve consists out of x-values, y-values, linewidth, alpha, and linecolour. The default is [].
    vlines : list, optional
        List of x-values to plot vertical lines on. The default is [].
    hlines : list, optional
        List of a list of y-values and line color. The default is [].
    scatterpoints : list, optional
        First list index is channel, second is cluster. Cluster[1] is x-values, cluster[3] is y-values, cluster[4] is label. The default is [].
    colorcycle : cycle, optional
        Cycle object of itertools containing colour values to be cycled through. The default is itertools.cycle("rbymgc").
    title : string, optional
        String to set as title of the figure. The default is "".
    text : list, optional
        List containing a single string to be in the middle of the figure. The default is [].

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    #Set title
    canvas.fig.suptitle(title)
    #plot channel data in their respective plots
    for ii,chan in enumerate(data):
        canvas.axs[ii].plot(time, chan, color = color, lw=lw)
    #vertical lines are plotted in all channel plots
    for line in vlines:
        clr=next(colorcycle)
        for ii,_ in enumerate(data):
            canvas.axs[ii].axvline(line, color=clr)
    #horizontal lines are plotted in all channel plots
    for line in hlines:
        for ii,_ in enumerate(data):
            canvas.axs[ii].axhline(line[0], color=line[1])
    #in plot text
    for ii,plttext in enumerate(text):
        canvas.axs[ii].text(0.5,0.6,plttext,
                     horizontalalignment='center',
                     verticalalignment="center")
    #multiple lines per channel
    for ii,chan in enumerate(curves):
        for curve in chan:
            if curve[4]==[]:
                curve[4]=next(colorcycle)
            canvas.axs[ii].plot(curve[0],curve[1],lw=curve[2],alpha=curve[3],color=curve[4],label=curve[5])
    #x- and y-labels
    canvas.fig.text(0.01, 0.5, ylabel, va="center", rotation="vertical")
    canvas.fig.text(0.5, 0.02, xlabel, ha="center")
    for ii,chan in enumerate(scatterpoints):
        for clusterN in range(len(chan)):
            canvas.axs[ii].scatter(scatterpoints[ii][clusterN][1] , scatterpoints[ii][clusterN][3], color = next(colorcycle), marker='o', label=scatterpoints[ii][clusterN][4])
    if legend:
        for ii in range(len(canvas.axs)):
            canvas.axs[ii].legend(frameon=False, loc="lower right")
    if xlim:
        canvas.axs[0].set_xlim([xlim[0][0],xlim[1][-1]])
    return canvas
def PlotHistFigure(canvas, data, bins, weights, xlabel="", ylabel="", *, legend=False, title="", colorcycle=itertools.cycle("rbymgc")):
    """
    Function to create a histogram.

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    data : Array of int64
        Array containing y-values per channel per cluster. First index contains y-values, second is cluster info.
    bins : Array of float64
        Bin sizes to subdivide data in.
    weights : list
        List of array of float64 per channel per cluster. Sum of weight per channel per cluster equals to 1.
    xlabel : string, optional
        x-label for plot. The default is "".
    ylabel : string, optional
        y-label for plot. The default is "".
    legend : bool, optional
        Denotes if a legend should be added. The default is False.
    title : string, optional
        String to set as title of the figure. The default is "".
    colorcycle : cycle, optional
        Cycle object of itertools containing colour values to be cycled through. The default is itertools.cycle("rbymgc").

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    canvas.fig.suptitle(title)
    for ii, chan in enumerate(data):
        for jj, spikeset in enumerate(chan):
            if len(data[ii][jj][0]):
                canvas.axs[ii].hist(spikeset[0], bins, weights=weights[ii][jj], color = next(colorcycle), alpha=0.5, label=f'{data[ii][jj][1]}', ec='black')
    canvas.fig.text(0.01, 0.5, ylabel, va="center", rotation="vertical")
    canvas.fig.text(0.5, 0.02, xlabel, ha="center")
    if legend:
        for ii in range(len(canvas.axs)):    
            canvas.axs[ii].legend(frameon=False)
    return canvas

def PlotWholeRecording(canvas, data, markers, time, colorSTR, *, channels=[1], title="Whole"):
    """
    Plot whole recording

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    data : Array of int64
        Array containing y-values per channel.
    markers : defaultdict
        Dictionary with marker numbers as keys, and marker time stamps as values.
    time : Array of float64
        Array containing x-values per channel. First index is channel, second contains x-values.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Whole".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    colors=itertools.cycle(colorSTR)
    vlines=[]
    for key in markers.keys():
        if len(markers[key])==1:
            vlines.append(markers[key])
        else:
            [vlines.append(submark) for submark in markers[key]]
    
    canvas=PlotDataFigure(canvas, data, time, "Time (s)", "Amplitude (a.u.)", "k", colorcycle=colors, vlines=vlines, title=f"{title} recording (ch{channels})")
    return canvas

def PlotPartial(canvas, markers, DataSelection, time, xlim, colorSTR, cutoff=[], thresholdsSTR="", *, channels=[1], title="Partial"):
    """
    Function to create a plot of the selected time frames

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    time : Array of float64
         Array containing x-values per channel. First index is channel, second contains x-values.
    DataSelection : list
         A list containing the signal data in the selected time frames per channel.
    xlim : list, optional
         List of a list of start times and a list of stop times for the time frames. x limit will be set from the first start value to the last stop value.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    cutoff : list, optional
        List with the cutoff value. The default is [].
    thresholdsSTR : TYPE, optional
        String containing all the thresholds as integers. The default is "".
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Spike".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    if len(thresholdsSTR)==0: thresholdsSTR="1" #Default value if no threshold is given
    thresholdstmp=[int(th) for th in re.split(r"\b\D+", thresholdsSTR) if th] #regular expression to filter out all numbers and convert each to int
    thresholds=list(set(thresholdstmp))
    thresholds.sort()
    thresholds=thresholds[::-1] #reverse the list
    #Plot the selected data
    colors=itertools.cycle(colorSTR)
    vlines=[]
    for key in markers.keys():
        if len(markers[key])==1:
            vlines.append(markers[key])
        else:
            [vlines.append(submark) for submark in markers[key]]
    hlines=[[thresh, next(colors)] for thresh in thresholds]
    colors=itertools.cycle(colorSTR)
    if cutoff:
        hlines.append([cutoff[0], "r"])
    canvas=PlotDataFigure(canvas, DataSelection, time, "Time (s)", "Amplitude (a.u.)", "k", hlines=hlines, xlim=xlim, colorcycle=colors, vlines=vlines, title=f"{title} recording (ch{channels})")
    return canvas

def SpikeDetection(canvas, clusters, time, DataSelection, xlim, colorSTR, cutoff=[], *, channels=[1], title="Spike"):
    """
    Function to create a plot showing the detected spikes.

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    time : Array of float64
         Array containing x-values per channel. First index is channel, second contains x-values.
    DataSelection : list
         A list containing the signal data in the selected time frames per channel.
    xlim : list, optional
         List of a list of start times and a list of stop times for the time frames. x limit will be set from the first start value to the last stop value.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    cutoff : list, optional
        List with the cutoff value. The default is [].
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Spike".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    colors=itertools.cycle(colorSTR)
    # Last, create the plot which indicates which spike belongs to which cluster
    if cutoff:
        cutoff[0]=[cutoff[0],"r"]
    canvas=PlotDataFigure(canvas, DataSelection, time, "Time (s)", "Amplitude (a.u.)", "k", hlines=cutoff, legend=[[f"T{clus[4][9:]}" for clus in ch] for ch in clusters], scatterpoints=clusters, xlim=xlim, colorcycle=colors, title=f"{title} sorting (ch{channels})")
    return canvas

def AverageWaveForm(canvasses, clusters, framerate, DataSelection, *, channels=[1], title="Average"):
    """
    Function to create plots for the average waveform per cluster per channel

    Parameters
    ----------
    canvassen : list
        A list of figures in which the data will be plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    framerate : int
        Sampling rate of the data.
    DataSelection : list
        A list containing the signal data in the selected time frames per channel.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set a part of the title of the figure. The default is "Average".

    Returns
    -------
    canvassen : list
        List of the figures in which the data has been plotted.
        canvassen[N].fig is a matplotlib figure and canvassen[N].axs is a list of matplotlib axes.
    clus : list
        A list of the channels and clusters per plot.

    """
    min_val = 5 # time in ms
    max_val = 10 # time in ms
    wvf_x = np.arange(-min_val, max_val, 1/framerate*1000) # time in ms
    n_cnv=0
    clus=[]
    for ii, chan in enumerate(clusters):
        for cl in chan:
            all_wvf_cl = []
            all_wvf_cl_std = []
            wvf_y=False
            for spike in cl[1]:
                #wvf_y is the amplitude per time point and therefor should be equal in length to wvvf_x    
                wvf_y = DataSelection[ii][int(spike*framerate-(min_val*framerate/1000)):int(spike*framerate+(max_val*framerate/1000))] # DataSelection is still in framerate, so convert the ms values back to secs
                #Had some problems with the length of wvf_y and wvf_x not matching, solved by following if statement and by telling to not use first and last 0.5 seconds of data
                #if len(wvf_y)>len(wvf_x):
                #    wvf_y=wvf_y[0:len(wvf_x)]
                #all_wvf_cl.append([wvf_x,wvf_y,0.5,0.5,[]])
                if len(wvf_x)==len(wvf_y):
                    all_wvf_cl.append([wvf_x,wvf_y,0.5,0.3,[],[]])
            text=[]
            if all_wvf_cl:
                all_wvf_cl.append([wvf_x, np.nanmean([yy[1] for yy in all_wvf_cl], axis=0), 2, 1, 'r',[]])
                all_wvf_cl_std=[wvf_x, np.nanstd([yy[1] for yy in all_wvf_cl], axis=0)]
            else:
                text=[f"Not enough data\nGot {len(all_wvf_cl)} datapoints\nAtleast 1 datapoint is required."]
            canvasses[n_cnv]=PlotDataFigure(canvasses[n_cnv], [], [], "Time (ms)", "Amplitude (a.u.)", "k", curves=[all_wvf_cl], text=text, title=f"{title} waveforms (ch{channels}) {cl[4]}")
            clus.append(f"Average waveforms ch{ii+1} {cl[4]}")
            if all_wvf_cl_std:
                #canvasses[n_cnv].axs[0].fill_between(all_wvf_cl_std[0], all_wvf_cl[-1][1]-all_wvf_cl_std[1], all_wvf_cl[-1][1]+all_wvf_cl_std[1],
                #                                     facecolor='b')
                canvasses[n_cnv].axs[0].plot(all_wvf_cl_std[0], all_wvf_cl[-1][1]-all_wvf_cl_std[1], linewidth=1.5, alpha=1, color='orange')
                canvasses[n_cnv].axs[0].plot(all_wvf_cl_std[0], all_wvf_cl[-1][1]+all_wvf_cl_std[1], linewidth=1.5, alpha=1, color='orange')
            n_cnv+=1
    return canvasses, clus

def InterSpikeInterval(canvas, clusters, framerate, colorSTR, *, channels=[1], title="Interspike"):
    """
    Function to create a plot for interspike interval

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    framerate : int
        Sampling rate of the data.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Distribution".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    colors=itertools.cycle(colorSTR)
    #Extract timestamps of spikes and convert them to milliseconds
    spike_times=[[[[x*1000 for x in cl[1]],cl[4]] for cl in chan] for chan in clusters]
    #Interspike intervals
    isispike_times=[[[np.diff(cl[0]),cl[1]] for cl in chan] for chan in spike_times]
    #Create bins and weights
    if any([any([any(cl[0]) for cl in chan]) for chan in isispike_times]):
        maxval=[[max(cl[0], default=100) for cl in chan] for chan in isispike_times]
        maxval=int(math.ceil(max(sum(maxval, []))/100))*100
        bins=np.logspace(np.log10(1),np.log10(maxval),50) #20000 is 20 seconds
        weights=[[np.ones_like(spikeset[0])/len(spikeset[0]) for spikeset in ch] for ch in isispike_times]
        canvas=PlotHistFigure(canvas, isispike_times, bins, weights, xlabel="Interspike interval (ms)",
                           ylabel="Normalized distribution", title=f"{title} interval (ch{channels})",
                           colorcycle=colors, legend=True)
        for ii,_ in enumerate(canvas.axs):
            canvas.axs[ii].set_xscale('log')
    else:
        canvas=PlotHistFigure(canvas, isispike_times, [], [], xlabel="Interspike interval (ms)",
                           ylabel="Normalized distribution", title=f"{title} interval (ch{channels})",
                           colorcycle=colors, legend=True)
    return canvas

def AmplitudeDistribution(canvas, clusters, framerate, colorSTR, *, channels=[1], title="Distribution"):
    """
    Function for creating a plot for amplitude distribution

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    framerate : int
        Sampling rate of the data.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Distribution".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    colors=itertools.cycle(colorSTR)
    #Extract peak heights
    spike_amp_cl = [[[cl[2], cl[4]] for cl in chan] for chan in clusters] # spike amplitude in arbitrary units (a.u.)
    #Create bins and weights
    if any([any([any(cl[0]) for cl in chan]) for chan in spike_amp_cl]):
        maxval=[[max(cl[0], default=100) for cl in chan] for chan in spike_amp_cl]
        maxval=int(math.ceil(max(sum(maxval, []))/100))*100
        minval=[[min(cl[0], default=100) for cl in chan] for chan in spike_amp_cl]
        minval=int(math.floor(min(sum(minval, []))/100))*100
        bins=np.arange(minval,maxval,(maxval-minval)/40)
        weights=[[np.ones_like(spikeset[0])/len(spikeset[0]) for spikeset in ch] for ch in spike_amp_cl]
        #Create histogram
        canvas=PlotHistFigure(canvas, spike_amp_cl, bins, weights, xlabel="Amplitude (a.u.)",
                       ylabel="Normalized distribution", title=f"{title} of spike amplitude (ch{channels})",
                       colorcycle=colors, legend=True)
    else:
        canvas=PlotHistFigure(canvas, spike_amp_cl, [], [], xlabel="Amplitude (a.u.)",
                       ylabel="Normalized distribution", title=f"{title} of spike amplitude (ch{channels})",
                       colorcycle=colors, legend=True)
    return canvas

def AutoCorrelation(canvassen, clusters, framerate, colorSTR, intervalsize=5, *, channels=[1], title="Autocorrelogram"):
    """
    Function to create an autocorrelation plot per threshold.

    Parameters
    ----------
    canvassen : list
        A list of figures in which the data will be plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    framerate : int
        Sampling rate of the data.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    intervalsize : int, optional
        Amount of time in seconds before and after the spike in which to look for correlation. The default is 5.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Autocorrelogram".

    Returns
    -------
    canvassen : list
        List of the figures in which the data has been plotted.
        canvassen[N].fig is a matplotlib figure and canvassen[N].axs is a list of matplotlib axes.
    clus : list
        A list of the channels and clusters per plot.

    """
    colors=itertools.cycle(colorSTR)
    #Extract timestamps of spikes and convert to location
    spike_times=[[[[int(x*framerate) for x in cl[1]],cl[4]] for cl in chan] for chan in clusters]
    #Calculate the autocorrelation per cluster per channel
    autocorr = [[cross_correlation(spikeset[0], spikeset[0], intervalsize*1000) for spikeset in chan] for chan in spike_times]
    peakcounts=[[0 for cl in chan] for chan in autocorr]
    #Calculate total peaks and set the 0ms to 0 peaks for better readability
    for ii,chan in enumerate(autocorr):
        for jj,cl in enumerate(chan):
            peakcounts[ii][jj]=cl[int(len(cl)/2)]
            autocorr[ii][jj][int(len(cl)/2)]=0
    clus=[]
    n_cnv=0
    for ii, chan in enumerate(autocorr):
        for jj, cl in enumerate(chan):
            canvassen[n_cnv]=PlotDataFigure(canvassen[n_cnv], [cl], np.arange(-cl.size/2, cl.size/2)+0.5,
                             "Time (ms)", "# of spikes", "k", colorcycle=colors, title=f"{title} (ch{ii+1}, {clusters[ii][jj][4]})")

            clus.append(f'ch{channels[ii]}, {clusters[ii][jj][4]}')
            canvassen[n_cnv].axs[0].text(0.05, 0.93, f'N={peakcounts[ii][jj]}', transform=canvassen[n_cnv].axs[0].transAxes)
            n_cnv+=1
    return canvassen, clus

def CrossCorrelation(canvas, clusters, framerate, colorSTR, intervalsize=5, x1=[0, 0], x2=[0, 1], *, channels=[1], title="Crosscorrelogram"):
    """
    Function to create a cross correlation between 2 clusters. 

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    framerate : int
        Sampling rate of the data.
    colorSTR : dict, list, string
        Series of color values to cycle between.
    intervalsize : int, optional
        Amount of time in seconds before and after the spike in which to look for correlation. The default is 5.
    x1 : list, optional
        List of two integers. Determines which cluster from which channel is used.
        First integer is for the channel, the second for the cluster. The default is [0, 0].
    x2 : list, optional
        List of two integers. Determines which cluster from which channel is used.
        First integer is for the channel, the second for the cluster. The default is [0, 1].
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Crosscorrelogram".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    colors=itertools.cycle(colorSTR)
    #Extract timestamps of spikes and convert to location
    spike_times=[[[[int(x*framerate) for x in cl[1]],cl[4]] for cl in chan] for chan in clusters]
    if type(x1[0])==str:
        spikeset1=[spike*framerate for spike in x1[1]]
        tabtitle=f"{title} (ch{x1[0]+1}, ch{x2[0]+1} {clusters[x2[0]][x2[1]][4]})"
    else:
        spikeset1=spike_times[x1[0]][x1[1]][0]
        tabtitle=f"{title} (ch{x1[0]+1} {clusters[x1[0]][x1[1]][4]}, ch{x2[0]+1} {clusters[x2[0]][x2[1]][4]})"
    spikeset2=spike_times[x2[0]][x2[1]][0]
    crosscorr=cross_correlation(spikeset1, spikeset2, intervalsize*1000)
    canvas=PlotDataFigure(canvas, [crosscorr], np.arange(-crosscorr.size/2, crosscorr.size/2)+0.5,
                          "Time (ms)", "# of spikes", "k", colorcycle=colors, title=tabtitle)
    return canvas, tabtitle

def Spectrogram(canvas, data, framerate, time, *, channels=[1], title="Spectrogram"):
    """
    Function to create a spectrogram.

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    data : Array of int64
        Array containing y-values per channel.
    framerate : int
        Amount of data points per second.
    time : Array of float64
        Array containing x-values per channel. First index is channel, second contains x-values.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "Spectrogram".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.

    """
    canvas.fig.suptitle(f"{title} (ch{channels})")
    for ii,chan in enumerate(data):
        canvas.axs[ii].specgram(chan, Fs=framerate, cmap="rainbow")
    canvas.fig.text(0.01, 0.5, "Frequency (Hz)", va="center", rotation="vertical")
    canvas.fig.text(0.5, 0.02, "Time (s)", ha="center")
    return canvas

def ERPplots(canvas, data, markers, framerate, colorSTR, xmin=1, xmax=5, *, channels=[1], title="ERP"):
    """
    Function to plot ERP signal per marker signature.

    Parameters
    ----------
    canvas : class
        The figure in which the data is plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    data : Array of int64
        Array containing y-values per channel.
    markers : defaultdict
        Dictionary with marker numbers as keys, and marker time stamps as values.
    framerate : int
        Amount of data points per second.
            Sampling rate of the data.
        colorSTR : dict, list, string
    xmin : float, optional
        DESCRIPTION. The default is 0.5.
    xmax : float, optional
        DESCRIPTION. The default is 5.
    channels : list, optional
        List of channel numbers. The default is [1].
    title : string, optional
        String to set as title of the figure. The default is "ERP".

    Returns
    -------
    canvas : class
        The figure in which the data has been plotted.
        canvas.fig is a matplotlib figure and canvas.axs is a list of matplotlib axes.
    erpsignals : list
        List containing a dict with the average ERP signal for every marker per channel.

    """
    colors=itertools.cycle(colorSTR)
    mf_x = np.arange(-xmin, xmax, 1/framerate) # time in s
    all_avg_mf=[]
    for ii,chan in enumerate(data):
        all_avg_mf.append([])
        for marker in markers.keys():
            all_mf=np.empty((0,len(mf_x)))
            for mtime in markers[marker]:
                mf_y=np.array(data[ii][int(mtime*framerate-(xmin*framerate)):int(mtime*framerate+(xmax*framerate))])
                if len(mf_x)==len(mf_y):
                    all_mf=np.vstack((all_mf, mf_y))
            all_avg_mf[ii].append([mf_x, np.nanmean(all_mf, axis=0), 0.5, 0.5, [], f'Marker {marker}'])
    canvas=PlotDataFigure(canvas, [], [], "Time (s)", "Amplitude (a.u.)", "k", curves=all_avg_mf, title=f"{title} (ch{channels})", colorcycle=colors)
    colors=itertools.cycle(colorSTR)
    for ii in range(len(canvas.axs)):
        canvas.axs[ii].legend(frameon=False, loc="lower right")
    erpsignals=[]
    for ii, ch in enumerate(all_avg_mf):
        erpsignals.append({erp[5]: erp[1] for erp in ch})
        erpsignals[ii]["Time (s)"]=all_avg_mf[0][0][0]
    return canvas, erpsignals
    