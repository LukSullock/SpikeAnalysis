# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 21:16:47 2024

@author: LukSu
"""

from scipy.signal import butter, lfilter
from scipy import signal
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

# Define data path
data_file = 'c:/users/luksu/onedrive/documenten/school documenten/psychobiologie/stage/code/spikeanalysis/modules/analysis/Strijder.wav'

# Header has 16 kilobytes length
header_size   = 16 * 1024  

# Open file
sf, rec = sp.io.wavfile.read("Gabcis.wav")

data=[]
[data.append(ch[0]) for ch in rec]

data=np.array(data[0:100000])

# Determine duration of recording in seconds
dur_sec = data.shape[0]/sf

# Create time vector
time = np.linspace(0, dur_sec,data.shape[0])

# Plot first second of data
fig, ax = plt.subplots(figsize=(15, 5))
ax.plot(time[0:sf], data[0:sf])
ax.set_title('Broadband; Sampling Frequency: {}Hz'.format(sf), fontsize=23)
ax.set_xlim(0, time[sf])
ax.set_xlabel('time [s]', fontsize=20)
ax.set_ylabel('amplitude [A.U.]', fontsize=20)
plt.show()

#%%
def filter_data(data, low, high, sf, order=2):
    # Determine Nyquist frequency
    nyq = sf/2

    # Set bands
    low = low/nyq
    high = high/nyq

    # Calculate coefficients
    b, a = butter(order, [low, high], btype='band')

    # Filter signal
    filtered_data = lfilter(b, a, data)

    return filtered_data

low=1
high=49

spike_data = filter_data(data, low=low, high=high, sf=sf)

# Plot signals
fig, ax = plt.subplots(2, 1, figsize=(15, 5))
ax[0].plot(time[0:sf], data[0:sf])
ax[0].set_xticks([])
ax[0].set_title('Broadband', fontsize=23)
ax[0].set_xlim(0, time[sf])
ax[0].set_ylabel('amplitude [A.U.]', fontsize=16)
ax[0].tick_params(labelsize=12)

ax[1].plot(time[0:sf], spike_data[0:sf])
ax[1].set_title(f'Spike channel [{low} to {high}Hz]', fontsize=23)
ax[1].set_xlim(0, time[sf])
ax[1].set_xlabel('time [s]', fontsize=20)
ax[1].set_ylabel('amplitude [A.U.]', fontsize=16)
ax[1].tick_params(labelsize=12)
plt.show()

#%%
# highpass=12
# nyq=0.5*sf
# b, a = signal.butter(2, highpass/nyq, btype='highpass')
# spike_data=signal.filtfilt(b, a, data)


b, a= signal.iirnotch(50, 30, sf)
spike_data=signal.filtfilt(b,a, data)

# Plot signals
fig, ax = plt.subplots(2, 1, figsize=(15, 5))
ax[0].plot(time[0:sf], data[0:sf])
ax[0].set_xticks([])
ax[0].set_title('Broadband', fontsize=23)
ax[0].set_xlim(0, time[sf])
ax[0].set_ylabel('amplitude [A.U.]', fontsize=16)
ax[0].tick_params(labelsize=12)

ax[1].plot(time[0:sf], spike_data[0:sf])
ax[1].set_title('Spike channel [50Hz filter]', fontsize=23)
ax[1].set_xlim(0, time[sf])
ax[1].set_xlabel('time [s]', fontsize=20)
ax[1].set_ylabel('amplitude [A.U.]', fontsize=16)
ax[1].tick_params(labelsize=12)
plt.show()

#%%
def get_spikes(data, spike_window=80, tf=5, offset=10, max_thresh=350):

    # Calculate threshold based on data mean
    thresh = np.mean(np.abs(data)) *tf

    # Find positions wherere the threshold is crossed
    pos = np.where(data > thresh)[0]
    pos = pos[pos > spike_window]

    # Extract potential spikes and align them to the maximum
    spike_samp = []
    wave_form = np.empty([1, spike_window*2])
    for i in pos:
        if i < data.shape[0] - (spike_window+1):
            # Data from position where threshold is crossed to end of window
            tmp_waveform = data[i:i+spike_window*2]

            # Check if data in window is below upper threshold (artifact rejection)
            if np.max(tmp_waveform) < max_thresh:
                # Find sample with maximum data point in window
                tmp_samp = np.argmax(tmp_waveform) +i

                # Re-center window on maximum sample and shift it by offset
                tmp_waveform = data[tmp_samp-(spike_window-offset):tmp_samp+(spike_window+offset)]

                # Append data
                spike_samp = np.append(spike_samp, tmp_samp)
                wave_form = np.append(wave_form, tmp_waveform.reshape(1, spike_window*2), axis=0)

    # Remove duplicates
    ind = np.where(np.diff(spike_samp) > 1)[0]
    spike_samp = spike_samp[ind]
    wave_form = wave_form[ind]

    return spike_samp, wave_form

spike_samp, wave_form = get_spikes(np.array(data), max_thresh=700, spike_window=50, tf=3, offset=0)

np.random.seed(10)
fig, ax = plt.subplots(figsize=(15, 5))

for i in range(100):
    spike = np.random.randint(0, wave_form.shape[0])
    ax.plot(wave_form[spike, :])

ax.set_xlim([0, 90])
ax.set_xlabel('# sample', fontsize=20)
ax.set_ylabel('amplitude [A.U]', fontsize=20)
ax.set_title('spike waveforms', fontsize=23)
plt.show()
#%%
import sklearn as sk
from sklearn.decomposition import PCA

# Apply min-max scaling
scaler= sk.preprocessing.MinMaxScaler()
dataset_scaled = scaler.fit_transform(wave_form)

# Do PCA
pca = PCA(n_components=12)
pca_result = pca.fit_transform(dataset_scaled)

# Plot the 1st principal component aginst the 2nd and use the 3rd for color
fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(pca_result[:, 0], pca_result[:, 1], c=pca_result[:, 2])
ax.set_xlabel('1st principal component', fontsize=20)
ax.set_ylabel('2nd principal component', fontsize=20)
ax.set_title('first 3 principal components', fontsize=23)

fig.subplots_adjust(wspace=0.1, hspace=0.1)
plt.show()

#%%
def k_means(data, num_clus=3, steps=200):

    # Convert data to Numpy array
    cluster_data = np.array(data)

    # Initialize by randomly selecting points in the data
    center_init = np.random.randint(0, cluster_data.shape[0], num_clus)

    # Create a list with center coordinates
    center_init = cluster_data[center_init, :]

    # Repeat clustering  x times
    for _ in range(steps):

        # Calculate distance of each data point to cluster center
        distance = []
        for center in center_init:
            tmp_distance = np.sqrt(np.sum((cluster_data - center)**2, axis=1))

            # Adding smalle random noise to the data to avoid matching distances to centroids
            tmp_distance = tmp_distance + np.abs(np.random.randn(len(tmp_distance))*0.0001)
            distance.append(tmp_distance)

        # Assign each point to cluster based on minimum distance
        _, cluster = np.where(np.transpose(distance == np.min(distance, axis=0)))

        # Find center of mass for each cluster
        center_init = []
        for i in range(num_clus):    
            center_init.append(cluster_data[cluster == i, :].mean(axis=0).tolist())

    return cluster, center_init, distance

max_num_clusters = 15

average_distance = []
for run in range(20):
    tmp_average_distance = []
    for num_clus in range(1, max_num_clusters +1):
        cluster, centers, distance = k_means(pca_result, num_clus)
        tmp_average_distance.append(np.mean([np.mean(distance[x][cluster==x]) for x in range(num_clus)], axis=0))
    average_distance.append(tmp_average_distance)

fig, ax = plt.subplots(1, 1, figsize=(15, 5))
ax.plot(range(1, max_num_clusters +1), np.mean(average_distance, axis=0))
ax.set_xlim([1, max_num_clusters])
ax.set_xlabel('number of clusters', fontsize=20)
ax.set_ylabel('average inter cluster distance', fontsize=20)
ax.set_title('Ellbow point', fontsize=23)
plt.show()

#%%
num_clus = 4
cluster, centers, distance = k_means(pca_result, num_clus)

# Plot the result
fig, ax = plt.subplots(1, 2, figsize=(15, 5))
ax[0].scatter(pca_result[:, 0], pca_result[:, 1], c=cluster)
ax[0].set_xlabel('1st principal component', fontsize=20)
ax[0].set_ylabel('2nd principal component', fontsize=20)
ax[0].set_title('clustered data', fontsize=23)

time = np.linspace(0, wave_form.shape[1]/sf, wave_form.shape[1])*1000
for i in range(num_clus):
    cluster_mean = wave_form[cluster==i, :].mean(axis=0)
    cluster_std = wave_form[cluster==i, :].std(axis=0)

    ax[1].plot(time, cluster_mean, label='Cluster {}'.format(i))
    ax[1].fill_between(time, cluster_mean-cluster_std, cluster_mean+cluster_std, alpha=0.15)

ax[1].set_title('average waveforms', fontsize=23)
ax[1].set_xlim([0, time[-1]])
ax[1].set_xlabel('time [ms]', fontsize=20)
ax[1].set_ylabel('amplitude [A.U.]', fontsize=20)

plt.legend()
plt.show()

#%%
combine_clusters = [0, 2]
combined_waveforms_mean = wave_form[[x in combine_clusters for x in cluster], :].mean(axis=0)
combined_waveforms_std = wave_form[[x in combine_clusters for x in cluster], :].std(axis=0)

combine_clusters = [1, 2]
combined_waveforms_mean2 = wave_form[[x in combine_clusters for x in cluster], :].mean(axis=0)
combined_waveforms_std2 = wave_form[[x in combine_clusters for x in cluster], :].std(axis=0)

fig, ax = plt.subplots(1, 1, figsize=(8, 5))
ax.plot(time, combined_waveforms_mean, label='Cluster 1')
ax.fill_between(time, combined_waveforms_mean-combined_waveforms_std, combined_waveforms_mean+combined_waveforms_std,
                alpha=0.15)

ax.plot(time, combined_waveforms_mean2, label='Cluster 2')
ax.fill_between(time, combined_waveforms_mean2-combined_waveforms_std2, combined_waveforms_mean2+combined_waveforms_std2,
                alpha=0.15)

ax.set_title('average waveforms', fontsize=23)
ax.set_xlim([0, time[-1]])
ax.set_xlabel('time [ms]', fontsize=20)
ax.set_ylabel('amplitude [A.U.]', fontsize=20)

plt.legend()
plt.show()
