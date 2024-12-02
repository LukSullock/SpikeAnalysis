# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 22:15:36 2024

@author: LukSu
"""

import serial
import numpy as np
import matplotlib.pyplot as plt
from serial.tools import list_ports

#%% Process function
def process_data(bdata):
    rawdata = np.array(bdata)
    data = np.zeros(0)
    ii = 0
    while ii < len(rawdata) - 1:
        if rawdata[ii] > 127:
            #Extract one sample from two bytes.
            int_processed=(np.bitwise_and(rawdata[ii], 127)) * 128
            ii += 1
            int_processed+=rawdata[ii]
            #Allocates, fills and returns new array.
            data=np.append(data, int_processed)
        ii+=1
    return data

#%% Main functions
def Read_data():
    # Read data from SpikerBox into a buffer of size input_buffer_size.
    byte_data = s.read(inputbuffer)
    # Cast to list of ints.
    byte_data = [int(byte_data[i]) for i in range(len(byte_data))]
    # Process with above function.
    data = process_data(byte_data)
    print(f'Data from serial: {str(data[0:4])[:-1]} ... ] (length {len(data)})')


#%% Check this in apple and windows when connected to spikerbox
baudrate = 230400 #Spikerbox specification
ports = list_ports.comports()
print("Available ports:")
for port in ports:
    print(port)
cport = input("Choose port: ")
inputbuffer = 10000 # 20000 = 1 second
# Set maximum time to read the buffer for. None for no timeout.
timeout=inputbuffer/20000.0

try:
    ser = serial.Serial(port=cport, baudrate=baudrate)
    ser.set_buffer_size(rx_size=inputbuffer)
    ser.timeout = timeout
except serial.serialutil.SerialException:
    raise Exception(f'Could not open port {cport}.')

with ser as s:
    while True:
        # Read data from SpikerBox into a buffer of size input_buffer_size.
        byte_data = s.read(inputbuffer)
        # Cast to list of ints.
        byte_data = [int(byte_data[i]) for i in range(len(byte_data))]
        # Process with above function.
        data = process_data(byte_data)
        print(f'Data from serial: {str(data[0:4])[:-1]} ... ] (length {len(data)})')





#%%
def read_arduino(ser,inputBufferSize):
    data = ser.read(inputBufferSize)
    out =[(int(data[i])) for i in range(0,len(data))]
    return out

# Read example data
baudrate = 230400 #Spikerbox specification
cport = 'COM12'  # set the correct port before you run it
#cport = '/dev/tty.usbmodem141101'  # set the correct port before run it
ser = serial.Serial(port=cport, baudrate=baudrate)
# take example data
inputBufferSize = 10000 # 20000 = 1 second
ser.timeout = inputBufferSize/20000.0  # set read timeout
#ser.set_buffer_size(rx_size = inputBufferSize)
data = read_arduino(ser,inputBufferSize)
data_plot = process_data(data)
plt.figure()
plt.plot(data_plot)
plt.show()

#%%
# this initializes the animated plot
fig = plt.figure()
ax = fig.add_subplot(111)
plt.ion()

fig.show()
fig.canvas.draw()

#%%
# take continuous data stream 
inputBufferSize = 10000 # keep betweein 2000-20000
ser.timeout = inputBufferSize/20000.0  # set read timeout, 20000 is one second
#this is the problem line on the mac
# ser.set_buffer_size(rx_size = inputBufferSize)


total_time = 20.0; # time in seconds [[1 s = 20000 buffer size]]
max_time = 10.0; # time plotted in window [s]
N_loops = 20000.0/inputBufferSize*total_time

T_acquire = inputBufferSize/20000.0    # length of time that data is acquired for 
N_max_loops = max_time/T_acquire    # total number of loops to cover desire time window

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
plt.ion()
fig.show()
fig.canvas.draw()

for k in range(0,int(N_loops)):
    data = read_arduino(ser,inputBufferSize)
    data_temp = process_data(data)
    if k <= N_max_loops:
        if k==0:
            data_plot = data_temp
        else:
            data_plot = np.append(data_temp,data_plot)
        t = (min(k+1,N_max_loops))*inputBufferSize/20000.0*np.linspace(0,1,len(data_plot))
    else:
        data_plot = np.roll(data_plot,len(data_temp))
        data_plot[0:len(data_temp)] = data_temp
    t = (min(k+1,N_max_loops))*inputBufferSize/20000.0*np.linspace(0,1,len(data_plot))

    
#    plt.xlim([0,max_time])
    ax1.clear()
    ax1.set_xlim(0, max_time)
    plt.xlabel('time [s]')
    ax1.plot(t,data_plot)
    fig.canvas.draw()    
    plt.show()

#%%
# close serial port if necessary
if ser.read():
    ser.flushInput()
    ser.flushOutput()
    ser.close()
