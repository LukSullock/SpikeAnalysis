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
import numpy as np

def PlotDataFigure(canvas, data, time, xlabel="", ylabel="", color="k", *, legend=False, xlim=False, lw=1, curves=[], vlines=[],hlines=[], scatterpoints=[], colorcycle=itertools.cycle("rbymgc"), title="", text=[]):
    canvas.fig.suptitle(title)
    for ii,chan in enumerate(data):
        canvas.axs[ii].plot(time, chan, color = color, lw=lw)
    for line in vlines:
        clr=next(colorcycle)
        for ii,_ in enumerate(data):
            canvas.axs[ii].axvline(line, color=clr)
    for line in hlines:
        clr='r'
        for ii,_ in enumerate(data):
            canvas.axs[ii].axhline(line, color=clr)
    for ii,plttext in enumerate(text):
        canvas.axs[ii].text(0.5,0.6,plttext,
                     horizontalalignment='center',
                     verticalalignment="center")
    for ii,chan in enumerate(curves):
        for curve in chan:
            if curve[4]==[]:
                curve[4]=next(colorcycle)
            canvas.axs[ii].plot(curve[0],curve[1],lw=curve[2],alpha=curve[3],color=curve[4])
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
def PlotHistFigure(canvas, data, bins, weights, framerate, xlabel="", ylabel="", *, legend=False, title="", colorcycle=itertools.cycle("rbymgc"), normed=True):
    canvas.fig.suptitle(title)
    for ii, chan in enumerate(data):
        for jj, spikeset in enumerate(chan):
            if len(data[ii][jj][0]):
                canvas.axs[ii].hist(spikeset[0], bins, weights=weights[ii][jj], density=True, color = next(colorcycle), alpha=0.5, label=f'{data[ii][jj][1]}', ec='black')
    canvas.fig.text(0.01, 0.5, ylabel, va="center", rotation="vertical")
    canvas.fig.text(0.5, 0.02, xlabel, ha="center")
    if legend:
        for ii in range(len(canvas.axs)):    
            canvas.axs[ii].legend(frameon=False)
    return canvas

def PlotWholeRecording(canvas, data, markers, time, colorSTR, *, channels=[1], title="Whole"):
    colors=itertools.cycle(colorSTR)
    vlines=[]
    for key in markers.keys():
        if len(markers[key])==1:
            vlines.append(markers[key])
        else:
            [vlines.append(submark) for submark in markers[key]]
    
    canvas=PlotDataFigure(canvas, data, time, "Time (s)", "Amplitude (a.u.)", "k", colorcycle=colors, vlines=vlines, title=f"{title} recording (ch{channels})")
    return canvas

def PlotPartial(canvas, markers,DataSelection,time,xlim,colorSTR, *, channels=[1], title="Partial"):
    #Plot the selected data
    colors=itertools.cycle(colorSTR)
    vlines=[]
    for key in markers.keys():
        if len(markers[key])==1:
            vlines.append(markers[key])
        else:
            [vlines.append(submark) for submark in markers[key]]
    canvas=PlotDataFigure(canvas, DataSelection, time, "Time (s)", "Amplitude (a.u.)", "k", xlim=xlim, colorcycle=colors, vlines=vlines, title=f"{title} recording (ch{channels})")
    return canvas

def SpikeDetection(canvas, clusters, time, DataSelection, xlim, colorSTR, cutoff=[], *, channels=[1], title="Spike"):
    colors=itertools.cycle(colorSTR)
    # Last, create the plot which indicates which spike belongs to which cluster
    canvas=PlotDataFigure(canvas, DataSelection, time, "Time (s)", "Amplitude (a.u.)", "k", hlines=cutoff, legend=[[f"T{clus[4][9:]}" for clus in ch] for ch in clusters], scatterpoints=clusters, xlim=xlim, colorcycle=colors, title=f"{title} sorting (ch{channels})")
    return canvas

def AverageWaveForm(canvasses, framerate, clusters, DataSelection, *, channels=[1], title="Average"):
    min_val = 5 # time in ms
    max_val = 10 # time in ms
    wvf_x = np.arange(-min_val, max_val, 1/framerate*1000) # time in ms
    n_cnv=0
    clus=[]
    for ii, chan in enumerate(clusters):
        for cl in chan:
            all_wvf_cl = []
            wvf_y=False
            for spike in cl[1]: # Skip the first and last one to avoid errors as it might be too close to the edge to plot the whole waveform
                #wvf_y is the amplitude per time point and therefor should be equal in length to wvvf_x    
                wvf_y = DataSelection[ii][int(spike*framerate-(min_val*framerate/1000)):int(spike*framerate+(max_val*framerate/1000))] # DataSelection is still in framerate, so convert the ms values back to secs
                #Had some problems with the length of wvf_y and wvf_x not matching, solved by following if statement and by telling to not use first and last 0.5 seconds of data
                #if len(wvf_y)>len(wvf_x):
                #    wvf_y=wvf_y[0:len(wvf_x)]
                #all_wvf_cl.append([wvf_x,wvf_y,0.5,0.5,[]])
                if len(wvf_x)==len(wvf_y):
                    all_wvf_cl.append([wvf_x,wvf_y,0.5,0.5,[]])
            text=[]
            if all_wvf_cl:
                all_wvf_cl.append([wvf_x, np.mean([yy[1] for yy in all_wvf_cl], axis=0), 2, 1, 'r'])
            else:
                text=[f"Not enough data\nGot {len(all_wvf_cl)} datapoints\nAtleast 1 datapoint is required.\nPeaks within the first {min_val}ms and last {max_val}ms of the selected data are skipped."]
            canvasses[n_cnv]=PlotDataFigure(canvasses[n_cnv], [], [], "Time (ms)", "Amplitude (a.u.)", "k", curves=[all_wvf_cl], text=text, title=f"{title} waveforms (ch{channels}) {cl[4]}")
            clus.append(f"Average waveforms ch{ii+1} {cl[4]}")
            n_cnv+=1
    return canvasses, clus

def InterSpikeInterval(canvas, clusters,framerate,colorSTR, *, channels=[1], title="Interspike"):
    colors=itertools.cycle(colorSTR)
    #Extract timestamps of spikes and convert them to milliseconds
    spike_times=[[[[x*1000 for x in cl[1]],cl[4]] for cl in chan] for chan in clusters]
    #average interspike interval, only used to check if there was enough data
    isispike_times=[[[np.diff(cl[0]),cl[1]] for cl in chan] for chan in spike_times]
    #Create bins and weights
    maxval=[[max(cl[0]) for cl in chan] for chan in isispike_times]
    maxval=int(math.ceil(max(sum(maxval, []))/100))*100
    bins=np.logspace(np.log10(1),np.log10(20000),50) #20000 is 20 seconds
    weights=[[np.ones_like(spikeset[0])/len(spikeset[0]) for spikeset in ch] for ch in isispike_times]
    canvas=PlotHistFigure(canvas, isispike_times, bins, weights, framerate, xlabel="Interspike interval (ms)",
                       ylabel="Normalized distribution", title=f"{title} interval (ch{channels})",
                       colorcycle=colors, legend=True)
    for ii,_ in enumerate(canvas.axs):
        canvas.axs[ii].set_xscale('log')
    return canvas

def AmplitudeDistribution(canvas, clusters, framerate, colorSTR, *, channels=[1], title="Distribution"):
    colors=itertools.cycle(colorSTR)
    #Extract peak heights
    spike_amp_cl = [[[cl[2], cl[4]] for cl in chan] for chan in clusters] # spike amplitude in arbitrary units (a.u.)
    #Create bins and weights
    maxval=[[max(cl[0]) for cl in chan] for chan in spike_amp_cl]
    maxval=int(math.ceil(max(sum(maxval, []))/100))*100
    minval=[[min(cl[0]) for cl in chan] for chan in spike_amp_cl]
    minval=int(math.floor(min(sum(minval, []))/100))*100
    bins=np.arange(minval,maxval,(maxval-minval)/40)
    weights=[[np.ones_like(spikeset[0])/len(spikeset[0]) for spikeset in ch] for ch in spike_amp_cl]
    #Create histogram
    canvas=PlotHistFigure(canvas, spike_amp_cl, bins, weights, framerate, xlabel="Amplitude (a.u.)",
                   ylabel="Normalized distribution", title=f"{title} of spike amplitude (ch{channels})",
                   colorcycle=colors, legend=True)
    return canvas
