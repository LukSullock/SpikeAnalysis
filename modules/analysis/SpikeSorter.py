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
                peaks=np.append(peaks, np.array([[peaklocation], [data[peaklocation]]]), axis=1)
                #Reset peak finding variables
                peakmax=0
                peaklocation=0
                peakstart=False
    peakcount=len(peaks[0])
    peakdata=(peaks[0], {"peak_heights": peaks[1]})
    return peakdata, peakcount

def filter_data(data, fr, low=1, high=500, notch=50, order=2, notchfilter=False, bandfilter=False):
    """
    Function to filter signal data.

    Parameters
    ----------
    data : list
        List containing the signal data.
    fr : int
        Framerate of the data.
    low : int, optional
        Lower end of the band pass filter. The default is 1.
    high : int, optional
        Higher end of the band pass filter. The default is 500.
    notch : int, optional
        Notch filter frequency. The default is 50.
    order : int, optional
        Order o. The default is 2.
    notchfilter : bool, optional
        Determines if the notchfilter is applied. The default is False.
    bandfilter : bool, optional
        Determines if the band pass filter is applied. The default is False.

    Returns
    -------
    data : list
        List containing the filtered signal data.

    """
    from scipy.signal import butter, lfilter, iirnotch, filtfilt
    if notchfilter:
        #calculate notch filter coefficients
        b, a= iirnotch(notch, 30, fr)
        #apply notch filter
        data=filtfilt(b,a, data)
    if bandfilter:
        nyq = fr/2
        #set band filter range
        low = low/nyq
        high = high/nyq
        #calculate band filter coefficients
        b, a = butter(order, [low, high], btype='band')
        #apply band filter
        data = lfilter(b, a, data)
    return data
