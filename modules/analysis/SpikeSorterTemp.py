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
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy as sp

def find_peaks(data, threshold, offset=0, subthresh=0.75):
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
    peakcount=len(peaks)
    peakdata=(peaks[0], {"peak_heights": peaks[1]})
    return peakdata, peakcount

def Get_Peak_Data(peakdata, fulldata):
    
    return peakdata

# =============================================================================
# parameters for PCA
# 1. peak height: The height of each peak.
# 2. plateau size: Calculated plateau sizes.
# 3. widths: The widths for each peak in samples.
# 4. width heights: The height of the contour lines at which the widths where evaluated.
# 5. left ips: Interpolated positions of left and right intersection points of a horizontal line at the respective evaluation height.
# 6. right ips: Interpolated positions of left and right intersection points of a horizontal line at the respective evaluation height.
# 7. left edges: Indices of a peak’s edges
# 8. right edges: Indices of a peak’s edges
# 9. left bases: The peaks’ bases. The higher base of each pair is a peak’s lowest contour line.
#10. right bases: The peaks’ bases. The higher base of each pair is a peak’s lowest contour line.
#11. prominences: The calculated prominences for each peak.
# =============================================================================

def PCA_analysis(peakdata, labels):
    #PCA analysis
    df=pd.DataFrame(peakdata, labels)
    df=df.T
    df=StandardScaler().fit_transform(df)
    pca=PCA(n_components=len(labels))
    pcomp=pca.fit_transform(df)
    princidf=pd.DataFrame(data=pcomp)
    plt.scatter(princidf[0], princidf[1], c=princidf[2])

#%% Show data
fr, rec = sp.io.wavfile.read("Strijder.wav")
#data=[rec[:100000,ii] for ii in range(rec.shape[1])]
data=rec[:100000,0]
time=np.linspace(0, data.shape[0]/fr, data.shape[0])

fig, ax = plt.subplots(figsize=(15, 5))
ax.plot(time[0:fr], data[0:fr])
ax.set_title(f'Broadband; Sampling Frequency: {fr}Hz', fontsize=23)
ax.set_xlim(0, time[fr])
ax.set_xlabel('time [s]', fontsize=20)
ax.set_ylabel('amplitude [A.U.]', fontsize=20)
plt.show()

#%% Filter data
# from scipy import signal
# from scipy.signal import butter, lfilter
# def filter_data(data, low, high, sf, order=2):
#     # Determine Nyquist frequency
#     nyq = sf/2

#     # Set bands
#     low = low/nyq
#     high = high/nyq

#     # Calculate coefficients
#     b, a = butter(order, [low, high], btype='band')

#     # Filter signal
#     filtered_data = lfilter(b, a, data)
    
#     return filtered_data

# spike_data = filter_data(data, low=20, high=500, sf=fr)

# f0 = 50  # Frequency to be removed from signal (Hz)
# w0 = f0/(fr/2)  # Normalized Frequency
# Q = 30 # Quality factor

# # Design notch filter
# b, a = signal.iirnotch(w0, Q)

# # Filter signal
# spike_data = signal.lfilter(b, a, data)

# # Plot signals
# fig, ax = plt.subplots(2, 1, figsize=(15, 5))
# ax[0].plot(time[0:fr], data[0:fr])
# ax[0].set_xticks([])
# ax[0].set_title('Broadband', fontsize=23)
# ax[0].set_xlim(0, time[fr])
# ax[0].set_ylabel('amplitude [A.U.]', fontsize=16)
# ax[0].tick_params(labelsize=12)

# ax[1].plot(time[0:fr], spike_data[0:fr])
# ax[1].set_title('Spike channel [20 to 500Hz] and 50Hz notch filter', fontsize=23)
# ax[1].set_xlim(0, time[fr])
# ax[1].set_xlabel('time [s]', fontsize=20)
# ax[1].set_ylabel('amplitude [uV]', fontsize=16)
# ax[1].tick_params(labelsize=12)
# plt.show()

#%% Show spikesorting
threshold=500
subthresh=0.8
f=plt.figure()
#plt.scatter( px, py )
peaks,peakcount=find_peaks(data, threshold=threshold, subthresh=subthresh)
peaktimes,peakheights=peaks
plt.plot(data)
plt.hlines([threshold,0], xmin=0, xmax=100000, colors="k")
plt.hlines(subthresh*threshold, xmin=0, xmax=100000, colors="orange")
plt.hlines(0.75*threshold, xmin=0, xmax=100000, colors="orange")
plt.vlines(peaktimes, threshold*0.7, threshold*1.3, colors="r")

#%% Spikesorting+PCA
peaks,peakcount=find_peaks(data, threshold=threshold, subthresh=subthresh)


# =============================================================================
# parameters for PCA
# 1. peak height: The height of each peak.
# 2. plateau size: Calculated plateau sizes.
# 3. widths: The widths for each peak in samples.
# 4. width heights: The height of the contour lines at which the widths where evaluated.
# 5. left ips: Interpolated positions of left and right intersection points of a horizontal line at the respective evaluation height.
# 6. right ips: Interpolated positions of left and right intersection points of a horizontal line at the respective evaluation height.
# 7. left edges: Indices of a peak’s edges
# 8. right edges: Indices of a peak’s edges
# 9. left bases: The peaks’ bases. The higher base of each pair is a peak’s lowest contour line.
#10. right bases: The peaks’ bases. The higher base of each pair is a peak’s lowest contour line.
#11. prominences: The calculated prominences for each peak.
# =============================================================================










