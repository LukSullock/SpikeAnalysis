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
import traceback
from collections import defaultdict

    
def OpenRecording(folder, filename):
    """
    Function to load in data and markers.
    Accepted filenames are .wav, and .npz.

    Parameters
    ----------
    folder : String
        String of the folder path from where to load the file.
    filename : String
        String of the filename including extension.

    Returns
    -------
    data : Array of int64
        Array containing y-values per channel.
    markers : defaultdict
        Dictionary with marker numbers as keys, and marker time stamps as values.
    time : Array of float64
        Array containing x-values per channel. First index is channel, second contains x-values.
    framerate : int
        Sampling rate of the data.
    datatype : str
        String denoting the type of the data.
    history : list
        List containing all changes made to the original data.
    identifier : string
        String denoting the identifier of the data.
    channels : list
        List containing the available channels.
    nomarker : list
        Contains the FileNotFoundError traceback if there was no marker file found.

    """
    #import .wav file and corresponding marker file
    file = os.path.join(folder, filename)
    markername =f"{filename[:-4]}-events.txt"
    markerfile=os.path.join(folder, markername)
    defaults={"Datatype": "SpikerBox",
              "Data": [],
              "Markers": defaultdict(list),
              "Clusters": [],
              "Time": [],
              "Framerate": 10000,
              "History": [],
              "Identifier": "001",
              "Channels": []
              }
    if ".wav" in filename: #SpikeRecorder Data (Backyard Brains, SpikerBox)
        rec = sp.io.wavfile.read(file)
        nomarker=False
        try:
            with open(markerfile, encoding="utf8") as csvfile:
                markersCSV=np.genfromtxt(csvfile, delimiter=',')
        except FileNotFoundError:
            nomarker=[traceback.format_exc()]
            markersCSV=[]
        #setup data from import .wav file
        framerate = rec[0]
        if len(rec[1].shape)==1: #when single channel recording
            data=np.array([rec[1]])
            ch=1
        elif rec[1].shape[0]>rec[1].shape[1]: #check if axes need to be swapped
            data=np.swapaxes(rec[1], 0, 1)
            ch=rec[1].shape[1]
        else:
            data=rec[1]
            ch=rec[1].shape[0]
        nframes = np.size(data, 1)
        time = np.array([x/framerate for x in np.arange(nframes)]) # in seconds
        #setup marker list
        markers=defaultdict(list)
        for key in markersCSV:
            markers[key[0]].append(key[1])
        datatype=defaults["Datatype"]
        clusters=defaults["Clusters"]
        history=defaults["History"]
        identifier=defaults["Identifier"]
        channels=[f'Channel {ii+1}' for ii in range(ch)]
    elif ".npz" in filename[-4:]: #SpikeAnalysis tool saved data
        npzfile=np.load(file, allow_pickle=True)
        loaddata=[]
        for key in defaults.keys():
            try:
                loaddata.append(npzfile[key])
            except KeyError:
                if key=="Channels":
                    loaddata.append([f'Channel {ii+1}' for ii in range(ch)])
                else:
                    loaddata.append(defaults[key])
        datatype=loaddata[0]
        data=loaddata[1]
        markerstmp=loaddata[2]
        markersdict=dict(enumerate(markerstmp.flatten(),1))[1]
        markers=defaultdict(list,markersdict)
        clusters=loaddata[3]
        time=loaddata[4]
        framerate=loaddata[5]
        history=loaddata[6]
        identifier=loaddata[7]
        channels=loaddata[8]
        if markers:
            nomarker=False
        else:
            nomarker=True
        
    return data, clusters, markers,time,framerate, datatype, history, identifier, channels, nomarker

def find_peaks(data, threshold, offset=0, subthresh=0.8):
    """
    Function to find peaks.
    Search method uses thresholds and a subthreshold proportion.
    Signal needs to go below the threshold before it searches for the first peak, and below the subthresh proportion of the threshold for subsequent peaks.

    Parameters
    ----------
    data : list
        List containing the signal data.
    threshold : int
        Threshold for which peaks need to be found.
    offset : int, optional
        Signal off-set. The default is 0.
    subthresh : float, optional
        Proportion that determines how far the signal needs to go below the signal before the function searches for another peak. The default is 0.8.

    Returns
    -------
    peakdata : tuple
        Tuple containing a list of the peak times and a dictionary containing the peak heights.
    peakcount : int
        The amount of peaks found.

    """
    if threshold<0:
        threshold=abs(threshold)
        data=[val*-1 for val in data]
        negthresh=-1
    else:
        negthresh=1
    last=len(data)
    peaks=np.empty((2,0))
    peakstart=False
    peaklocation=0
    peakmax=threshold
    for ii, peak in enumerate(data):
        #only look for a peak if the data has gone below the threshold
        if peak<(threshold+offset):
            peakstart=True
        #Check if the peak is a local maximum, and exclude first and last values
        if ii>0 and ii<last-1 and peak>=threshold+offset:
            if peak>=data[ii-1] and peak>=data[ii+1] and peakstart:
                #Check if the peak is higher than last found peak
                if peak>peakmax:
                    peaklocation=ii
                    peakmax=peak
        #If the start of a peak has been found, check if the peak drops below half of the threshold
        if peaklocation:
            if data[ii-1]>=(subthresh*threshold+offset) and peak<(subthresh*threshold+offset) and peakstart:
                #Add the peaklocation and height of the highest point of the peak to the peaks array
                peaks=np.append(peaks, np.array([[peaklocation], [data[peaklocation]*negthresh]]), axis=1)
                #Reset peak finding variables
                peakmax=0
                peaklocation=0
                peakstart=False
    peakcount=len(peaks[0])
    peakdata=(peaks[0], {"peak_heights": peaks[1]})
    return peakdata, peakcount

def SpikeSorting(DataSelection,thresholds,subthresh,framerate,time,cutoff_thresh=False):
    """
    Function to sort spikes based on thresholds

    Parameters
    ----------
    DataSelection : list
        A list containing the signal data in the selected time frames per channel.
    thresholds : list
        List containing the thresholds, ordered from largest to smallest.
    subthresh : float
        Float determining how far the signal needs to go below the threshold before searching for a new spike.
    framerate : int
        Sampling rate of the data.
    time : Array of float64
        Array containing x-values per channel. First index is channel, second contains x-values.
    cutoff_thresh : int or bool
        Integer if the cut-off threshold is being used, otherwise the bool False. The default is False.

    Returns
    -------
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.

    """
    # First, get everything above cutoff if cutoff is given
    cutoff1=[[[]] for _ in range(len(DataSelection))]
    if type(cutoff_thresh)==int:
        for ii in range(len(DataSelection)):
            th = cutoff_thresh
            #cutoff1[ii] = sp.signal.find_peaks(DataSelection[ii], height=th, distance=distance*framerate, prominence=0)
            cutoff1[ii], _ = find_peaks(DataSelection[ii], threshold=th, subthresh=subthresh)
        
    cl2=[[] for _ in range(len(DataSelection))]
    maxval=[[] for _ in range(len(DataSelection))]
    #clusters: [[peak data], [time], [plot height of points], ["Cluster threshold {threshold}"]
    clusters=[[[[],[],[],[],np.array([th], dtype=np.float64)] for ii,th in enumerate(thresholds)] for _ in range(len(DataSelection))]
    maxsize=1
    for ii in range(len(DataSelection)):
        #Get largest peak of selected data
        cl2[ii]=np.nanmax(DataSelection[ii])
        maxval[ii]=cl2[ii]
        #Detect the other spikes per cluster
        for clusterN,th in enumerate(thresholds):
            #clusters[ii][clusterN][0] = sp.signal.find_peaks(DataSelection[ii], height=th, distance=distance*framerate)
            clusters[ii][clusterN][0],_ = find_peaks(DataSelection[ii], threshold=th, subthresh=subthresh)
            for peakN,x in enumerate(clusters[ii][clusterN][0][0]):
                if x not in cutoff1[ii][0] and not any(x in clusters[ii][jj][0][0] for jj in range(clusterN)):
                    clusters[ii][clusterN][1].append(x/framerate)
                    clusters[ii][clusterN][2].append(clusters[ii][clusterN][0][1]["peak_heights"][peakN])
            clusters[ii][clusterN][1]=np.array(clusters[ii][clusterN][1])
            clusters[ii][clusterN][2]=np.array(clusters[ii][clusterN][2])
            #y value for points denothing peaks above largest peak
            clusters[ii][clusterN][3] = np.ones(len(clusters[ii][clusterN][1] ))*maxval[ii]+(maxval[ii]/10*(clusterN+1))
            if len(clusters[ii][clusterN][0][0])>maxsize:
                maxsize=len(clusters[ii][clusterN][0][0])
    for ii in range(len(clusters)):
        for jj in range(len(clusters[ii])):
            clusters[ii][jj][0]=clusters[ii][jj][0][0]
            for kk in range(len(clusters[ii][jj])):
                clusters[ii][jj][kk]=np.append(clusters[ii][jj][kk], np.zeros(maxsize-len(clusters[ii][jj][kk]))+np.nan)
    return clusters

def DataSelect(data,markers,framerate,times):
    """
    Depricated.
    
    Function to create a selection of the data.
    If no input was given, default to whole recording.

    Parameters
    ----------
    data : Array of int64
        Array containing y-values per channel.
    markers : defaultdict
        Dictionary with marker numbers as keys, and marker time stamps as values.
    framerate : int
        Sampling rate of the data.
    times : String
        String containing time frames. Different time frames should be seperated by 'and'.

    Returns
    -------
    [start_time,stop_time] : list
        A list containing all the start times and stop times of the individual time frames.
    DataSelection : list
        A list containing the signal data in the selected time frames per channel.
    markers : defaultdict
        Dictionary with marker numbers as keys, and marker time stamps as values.

    """
    #Get time frames
    times=times.split(" and ")
    for ii,art in enumerate(times):
        times[ii]=art.split(" to ")
    #If there is no given range, default to whole recording
    if not len(times[0][0]):
        times=[["0", f"{len(data[0])}"]]
    #Get the time stamps of markers when they are used
    for ii,th in enumerate(times):
        for jj,art in enumerate(th):
            #If a marker was given then use maker time, otherwise convert string to float.
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
    #Create lists for start and stop times
    start_time=[art[0] for art in times]
    stop_time=[art[1] for art in times]
    #Create selection of data
    DataSelection = np.empty((len(data),len(data[0])))
    DataSelection[:]=np.nan
    for ii in range(len(start_time)):
        for chan in range(len(DataSelection)):
            #Copy the data of the selected time windows from whole data variable to the dataselection variable
            DataSelection[chan][int(start_time[ii]*framerate):int(stop_time[ii]*framerate)]=data[chan][int(start_time[ii]*framerate):int(stop_time[ii]*framerate)]
    for marker in markers.keys():
        for ii in reversed(range(len(markers[marker]))):
            pop=True
            for jj, start in enumerate(start_time):
                if markers[marker][ii]>=start and markers[marker][ii]<=stop_time[jj]:
                    pop=False
            if pop: markers[marker].pop(ii)
    markers=defaultdict(None, {key: item for key, item in markers.items() if item})
    return [start_time,stop_time],DataSelection,markers

def SaveAll(data, folder, output):
    """
    For every cluster creates dataframes for the time in seconds where a spike occurred, start and stop times of data selection in seconds, hertz in /s and cut off threshold in a.u.
    Files are saved in the /saved directory in the path where main file is located
    1 csv file per cluster and 1 pdf file with all plots
    
    NOTE: Check for overwriting files does not happen in this function, but in the SavePlots function, see modules/GUI/GUIFunctions.

    Parameters
    ----------
    clusters : list
        A list containing all peaks above threshold height, timestamps of peaks, heights of peaks, height of spike marker per peak, and the threshold height per threshold per channel.
    erpsignals : list
        List containing a dict with the average ERP signal for every marker per channel.
    start_time : list
        List containing the start times of every time frame.
    stop_time : list
        List containing the stop times of every time frame.
    folder : String
        String of the folder path from where to save the file.
    output : string
        String containing the file identifier, which is included in every filename.
    cutoff_thresh : list
        List with the cutoff value. The default is [].
    channels : list
        List of channel numbers.

    """
    #Get cluster data
    clusters=data["Clusters"]
    start_time=0
    stop_time=0
    cutoff_thresh=0
    channels=[1,2]
    for jj,chan in enumerate(clusters):
        for ii,cl in enumerate(chan):
            oridf=pd.DataFrame({cl[4]: cl[1]})
            adddf=pd.DataFrame({"Start time": start_time,"Stop time":stop_time})
            meanhertz=len(cl[1])/(sum([stop_time[tt]-start_time[tt] for tt in range(len(start_time))]))
            meanhzdf=pd.DataFrame({"Frequency": [meanhertz]})
            # if cutoff_thresh:
            #     cutoff_thresh=cutoff_thresh[0]
            cutoffdf=pd.DataFrame({"Cut off threshold": cutoff_thresh})
            df1=pd.concat([oridf,adddf,meanhzdf,cutoffdf],axis=1)
            df1.to_csv(os.path.join(folder,f'spiketimes_{output}_channel{channels[jj]}_cluster{ii+1}.csv'),index=False)
