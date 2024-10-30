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
from scipy.signal import find_peaks as fp
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def find_peaks(data, threshold=1, prominence=0):
    """
    Function to find peaks in a dataset using thresholds and pca

    Parameters
    ----------
    data : List of integers holding peakheights.
    threshold : Minimum height to detect peaks.
    distance : Minimum distance between spikes in datapoints.

    Returns
    -------
    peaktimes : List of peaktimes in framerate
    
    """
    #Find peaks and peak data in given data
    peaktimes=fp(data, height=threshold, width=0, plateau_size=0)
    peakdata=[]
    peakdata.append(peaktimes[1]["peak_heights"])
    peakdata.append(peaktimes[1]["plateau_sizes"])
    peakdata.append(peaktimes[1]["widths"])
    peakdata.append(peaktimes[1]["width_heights"])
    peakdata.append(peaktimes[1]["left_ips"])
    peakdata.append(peaktimes[1]["right_ips"])
    peakdata.append(peaktimes[1]["left_edges"])
    peakdata.append(peaktimes[1]["right_edges"])
    peakdata.append(peaktimes[1]["left_bases"])
    peakdata.append(peaktimes[1]["right_bases"])
    peakdata.append(peaktimes[1]["prominences"])
    labels=["peak_heights","plateau_sizes", "widths", "width_heights",
            "left_ips", "right_ips", "left_edges", "right_edges", 
            "left_bases", "right_bases","prominences"]
    #Normalise peak data
    coeffvariance=[None for _ in range(len(peakdata))]
    for ii in reversed(range(len(peakdata))):
        mean=peakdata[ii].mean()
        std=peakdata[ii].std()
        if std!=0:
            peakdata[ii]=(peakdata[ii]-mean)/std
            coeffvariance
        else:
            peakdata.pop(ii)
            print(f'Removed variable: {labels.pop(ii)}')
    
    return peaktimes, peakdata, labels


data=[]
fr, rec = sp.io.wavfile.read("gabcis.wav")
[data.append(ch[0]) for ch in rec]
data=data[500:1000]
x1 = np.linspace(0, 100 * np.pi, num=2000)
x2 = np.linspace(0, 30 * np.pi, num=2000)
n = np.random.normal(scale=8, size=x1.size)
y = 100*np.sin(x1)+100*np.sin(x2)+ n

signal = np.int16(y)
signal=data
#plt.scatter( px, py )
f=plt.subplot(2,1,1)
plt.plot(signal)
msigabs=np.mean(np.abs(signal))
msig=np.mean(signal)
print(msig)
print(msigabs)
(peaktimes,peaktimesextra), peakdata, labels=find_peaks(signal, threshold=1, prominence=0)
prominences=peaktimesextra["prominences"]
print(np.mean(prominences))
print(np.std(prominences))
print(np.median(prominences))
print(np.percentile(prominences, [75,25]))
ymax=max(signal)*1.1
ypeaks=[ymax]*len(peaktimes)
plt.vlines(peaktimes, ymin=0, ymax=ypeaks, colors="r")
f=plt.subplot(2,1,2)
(peaktimes2,peaktimesextra2), peakdata, labels=find_peaks(signal, threshold=1, prominence=np.mean(prominences))
plt.plot(signal)
ypeaks=[ymax]*len(peaktimes2)
plt.vlines(peaktimes2, ymin=0, ymax=ypeaks, colors="r")


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










