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
import numpy as np
import scipy as sp
import pandas as pd
import os
import re
from matplotlib import pyplot as plt
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
matplotlib.rcParams['pdf.fonttype'] = 42 # necessary to make the text editable
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.use('QtAgg')
if int(np.__version__.split(".")[0])>1: np.set_printoptions(legacy='1.25')
import traceback
from collections import defaultdict

    
def OpenRecording(folder, filename):
    #import .wav file and corresponding marker file
    file = os.path.join(folder, filename)
    markername =f"{filename[:-4]}-events.txt"
    markerfile=os.path.join(folder, markername)
    rec = sp.io.wavfile.read(file)
    try:
        with open(markerfile, encoding="utf8") as csvfile:
            markersCSV=np.genfromtxt(csvfile, delimiter=',')
    except FileNotFoundError:
        markersCSV=[]
    
    #setup data from import .wav file
    framerate = rec[0]
    if np.int16==type(rec[1][0]): #when single channel recording
        data=[[point for point in rec[1]] for _ in range(1)]
    else: #with more than 1 channel recording
        data=[[point[chan-1] for point in rec[1]] for chan in range(len(rec[1][0]))]
    nframes = len(data[0])
    time = [x/framerate for x in np.arange(nframes)] # in seconds

    #setup marker list
    markers=defaultdict(list)
    for key in markersCSV:
        markers[key[0]].append(key[1])
    return data,markers,time,framerate
    
def DataSelect(data,markers,framerate,times):
    #Create a selection of the data, if no input was given, default to time frame between first and last 0.5 seconds,
    #time before chosen time frame needs to be longer than what min_val is assigned in SpikeSorterFunctions.AverageWaveForm, time after needs to be longer than max_val
    times=times.split(" and ")
    for ii,art in enumerate(times):
        times[ii]=art.split(" to ")
    #If there is no given range, default to whole recording (without starting and ending 0.5 seconds)
    if not len(times[0][0]):
        times=[["0.5", f"{len(data[0])/framerate-0.5}"]]
    #Get the time stamps of markers when they are used
    for ii,th in enumerate(times):
        for jj,art in enumerate(th):
            #If marker then use maker time, otherwise convert string to float
            if "m" in art or "M" in art:
                try:
                    times[ii][jj]=markers[int(times[ii][jj][-1])][0]
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
    
    #Create selection of data
    DataSelection = [[np.nan]*len(chan) for chan in data]
    for ii in range(len(start_time)):
        for chan in range(len(DataSelection)):
            DataSelection[chan][int(start_time[ii]*framerate):int(stop_time[ii]*framerate)]=data[chan][int(start_time[ii]*framerate):int(stop_time[ii]*framerate)]
    return [start_time,stop_time],DataSelection


def SpikeSorting(DataSelection,thresholdsSTR,distance,framerate,time, cutoff_thresh):
    if len(thresholdsSTR)==0: thresholdsSTR="1" #Default value if no threshold is given
    thresholdstmp=[int(th) for th in re.split(r"\b\D+", thresholdsSTR)] #regular expression to filter out all numbers and convert each to int
    thresholdstmp.sort()
    thresholdstmp=thresholdstmp[::-1] #reverse the list
    thresholds=list(set(thresholdstmp))
    # First, get everything above cutoff if cutoff is given
    cutoff1=[[[]] for _ in range(len(DataSelection))]
    if cutoff_thresh:
        for ii in range(len(DataSelection)):
            th = cutoff_thresh
            cutoff1[ii] = sp.signal.find_peaks(DataSelection[ii], height=th, distance=distance*framerate)
        
    cl2=[[] for _ in range(len(DataSelection))]
    maxval=[[] for _ in range(len(DataSelection))]
    #clusters: [[peak data], [time], [plot height of points], ["Cluster threshold {threshold}"]
    clusters=[[[[],[],[],f"Cluster threshold {th}"] for ii,th in enumerate(thresholds)] for _ in range(len(DataSelection))]
    #Get largest peak of selected data
    for ii in range(len(DataSelection)):
        cl2[ii]=sp.signal.find_peaks(DataSelection[ii], height=0, distance=distance*framerate)[1]["peak_heights"]
        maxvalN=np.argmax(cl2[ii])
        maxval[ii]=cl2[ii][maxvalN]

        # Then, detect the other spikes per cluster, 'Cluster #'
        for clusterN,th in enumerate(thresholds):
            clusters[ii][clusterN][0] = sp.signal.find_peaks(DataSelection[ii], height=th, distance=distance*framerate)
            for peakN,x in enumerate(clusters[ii][clusterN][0][0]):
                if x not in cutoff1[ii][0] and not any(x in clusters[ii][jj][0][0] for jj in range(clusterN)):
                    clusters[ii][clusterN][1].append(x/framerate) #+start_time[0]
            #y value for points denothing peaks above largest peak
            clusters[ii][clusterN][2] = np.ones(len(clusters[ii][clusterN][1] ))*maxval[ii]+(maxval[ii]/10*(clusterN+1))
    return clusters

def SaveAll(clusters,start_time,stop_time,folder,output,cutoff_thresh):
    #For every cluster creates dataframes for the time in seconds where a spike occurred, start and stop times of data selection in seconds, hertz in /s and cut off threshold in a.u.
    #Save files in path where main file is located
    #1 csv file per cluster and 1 pdf file with all plots
    #NOTE: there is no check for duplicate file names, old files will be overridden
    for jj,chan in enumerate(clusters):
        for ii,cl in enumerate(chan):
            oridf=pd.DataFrame({cl[3]: cl[1]})
            adddf=pd.DataFrame({"Start time": start_time,"Stop time":stop_time})
            meanhertz=len(cl[1])/(sum([stop_time[tt]-start_time[tt] for tt in range(len(start_time))]))
            meanhzdf=pd.DataFrame({"Frequency": [meanhertz]})
            cutoffdf=pd.DataFrame({"Cut off threshold": [cutoff_thresh]})
            df1=pd.concat([oridf,adddf,meanhzdf,cutoffdf],axis=1)
            df1.to_csv(os.path.join(folder,f'spiketimes_{output}_channel{jj+1}_cluster{ii+1}.csv'),index=False)
    p=PdfPages(os.path.join(folder,f"Plots_{output}.pdf"))
    figs=[plt.figure(n) for n in plt.get_fignums()]
    [fig.savefig(p, format='pdf') for fig in figs]
    p.close()



