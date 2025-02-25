# -*- coding: utf-8 -*-
"""
Author: LH
Date: 08.2023
Functionality: Generate CSV files fot stimulation mask (GammaSleep study)
Assumptions:
Notes: Adapted from https://github.com/tscnlab/LiDuSleep/blob/main/07_LightMask/csv/CSVGenerator.ipynb

"""


# %% Environment Setup

## Packages

import csv
import datetime
import numpy as np
import matplotlib.pyplot as plt


## Constants

# Today's date
today = datetime.datetime.now()
date = today.strftime("%Y") + today.strftime("%m") + today.strftime("%d")

# Flicker frequency = 40 Hz
flicker_freq = 40 

# Analog value corresponding to minimum illuminance of 0 lux
min_analog = 0

# Analog value corresponding to stim target illuminance of 20 lux
max_analog = 2000
    
# Frequency at which the Arduino reads CSV rows, in Hz
sample_rate = flicker_freq * 2 # For 40 Hz square-wave flicker, 40x ON + 40x OFF



# %% Function: header

"""
    Function to create CSV header.
    
    Input
    ----------
    date : str 
	Date of file generation [YYYYMMDD]
    
    sample_rate : int
    Frequency at which the Arduino reads CSV rows in Hz.
    
    nsamples : int
    Nr of CSV rows containing output data.
    
    nrepeat : int
    Nr of times the CSV should be iterated over.

    Output
    -------
    header : dict
	Header of the generated CSV file.

"""

def create_header(date,sample_rate,min_analog,max_analog,nsamples,nrepeat):
    
    header = {
            '% Date [YYYYMMDD]': date,
            '% Experimenter': 'LH',
            '% Experiment': 'GammaSleep',
            '% Condition': 'exp',
            '% Note': '',
            '%  ': '',
            '% Sample rate [Hz]': str(sample_rate),
            '% MinValue': str(min_analog),
            '% MaxValue': str(max_analog),
            '% NSamples': str(nsamples),    
            '% NRepeat': str(nrepeat),
            '% ': ''
        }
    
    return header



# %% Function: generate rampup data

"""
    Function to create stimulation data for rampup routine.
    
    Input
    ----------
    flicker_freq : int
	Flicker frequency (40 Hz).
    
    max_analog : int
    Analog value corresponding to stim target illuminance (20 lux).
    
    sample_rate : int
    Frequency at which the Arduino reads CSV rows, in Hz.

    Output
    -------
    data : ndarray
	CSV file content below header.
    
    nsamples : int
	Nr of CSV rows containing output data.
    
    nrepeat : int
	Nr of times the CSV should be iterated over.

"""

def create_data_rampup(flicker_freq,max_analog,sample_rate):

    ## Compute parameters

    # Duration of rampup in sec (=5 min)
    ramp_time = int(5 * 60)
    
    # Duration of post-ramp transition flicker time in sec
    flicker_time = 10
    
    # Nr. of samples for defined ramp data duration
    nsamples_ramp = int(sample_rate * ramp_time)
    
    # Nr. of samples including post-ramp transition flicker
    nsamples_flicker = int(sample_rate * flicker_time)
    
    # Nr. of flicker cycles for defined ramp data duration
    ncycles_ramp = flicker_freq * ramp_time
    
    # Nr. of flicker cycles for post-ramp transition flicker
    ncycles_flicker = flicker_freq * flicker_time

    # Nr. of repetitions (rampup once, then move to flicker)
    nrepeat = 1


    ## Required CSV format elements
    
    # Header row of data
    headers = ['Sample', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Channel5', 'Channel6', 'Trigger', 'Note']

    # Sample nrs
    sample_nrs = np.array([i for i in range(1, nsamples_ramp + nsamples_flicker + 1)])
    
    # Triggers (none)
    triggers = np.zeros((nsamples_ramp + nsamples_flicker, 5))
    
    # Notes (none)
    notes = np.array([''] * (nsamples_ramp + nsamples_flicker))


    ## Generate cosine ramp
    
    # Array of radians between pi (trough) & 2*pi (peak), with nr. of elements = nr. of cycles
    radians = np.array([i for i in np.arange(np.pi, np.pi*2, np.pi/(ncycles_ramp-0.5))]) # subtract 0.5 from ncycles to get 12k elements
    
    # Take cosine values of radians, with fitted amplitude & upward shift (for y in cosine shape)
    cosines = np.array([i for i in (max_analog/2) * np.cos(radians) + max_analog/2])
    
    # Round y values, as program only takes int values
    y_cos_int = np.round(cosines)
     
    
    ## Plot for visual inspection
    
    plt.figure()
    plt.plot(y_cos_int) 
    plt.title('Cosine ramp-up', size=30, y=1.05)
    plt.xlabel('Flicker cycles (0 - ' + str(ramp_time/60) + ' min)', size=20)
    plt.ylabel('Analog values', size=20)


    ## Transform into data array with flicker
    
    # Initialize data array (2 channels)
    ramp_up = np.zeros((nsamples_ramp,2))
    
    # Fill cycles with ON period from cosines_int, leave OFF period at 0
    i = 0
    while i in range(0, ncycles_ramp):
        
        ramp_up[i*2] = y_cos_int[i]
        i += 1
        
    
    ## Add 10 sec flicker after ramp for smoother transition to flicker
    
    # Data for 1 flicker cycle
    data_1_cycle = np.array([[max_analog,max_analog], [0,0]])

    # Data for full file 
    data_all_cycles = np.tile(data_1_cycle, (ncycles_flicker, 1))
    
    # Stack flicker onto ramp
    ramp_flicker = np.vstack([ramp_up, data_all_cycles])
                             

    ## Combine arrays
    
    # Sample nrs, data, notes
    data = np.c_[sample_nrs, ramp_flicker, triggers, notes]
    
    # Add headers
    data = np.vstack([headers,data])


    return data, nsamples_ramp + nsamples_flicker, nrepeat



# %% Function: generate flicker data

"""
    Function to create stimulation data for flicker routine.
    
    Input
    ----------
    flicker_freq : int
	Flicker frequency (40 Hz).
    
    max_analog : int
    Analog value corresponding to stim target illuminance (20 lux).
    
    sample_rate : int
    Frequency at which the Arduino reads CSV rows, in Hz.

    Output
    -------
    data : ndarray
	CSV file content below header.
    
    nsamples : int
	Nr of CSV rows containing output data.
    
    nrepeat : int
	Nr of times the CSV should be iterated over.

"""

def create_data_flicker(flicker_freq,max_analog,sample_rate):
    
    ## Compute parameters
    
    # Max. stim time in sec (8 hours)
    max_stim_time = int(8 * 60 * 60)
    
    # Duration of data file in sec
    data_file_time = 1
    
    # Nr. of samples for defined file duration
    nsamples = data_file_time * sample_rate

    # Nr. of repetitions for total stim time
    nrepeat = max_stim_time / data_file_time
    

    ## Required CSV format elements
    
    # Header row of data
    headers = ['Sample', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Channel5', 'Channel6', 'Trigger', 'Note']

    # Sample nrs
    sample_nrs = np.array([i for i in range(1, nsamples+1)])
    
    # Notes (none)
    notes = np.array([''] * nsamples)
    

    ## Generate data
    
    # Data for 1st flicker cycle (includes trigger)
    data_1st_cycle = np.array([[max_analog,max_analog,1,1,1,1,1], [0,0,0,0,0,0,0]])
    
    # Data for one cycle without trigger
    data_1_cycle_notrig = np.array([[max_analog,max_analog,0,0,0,0,0], [0,0,0,0,0,0,0]])

    # Data for 39 flicker cycles
    data_39_cycles = np.tile(data_1_cycle_notrig, (flicker_freq-1,1))
    
    # Combine 1st cycle with trigger with remaining 39 cycles without trigger
    data_all_cycles = np.vstack([data_1st_cycle,data_39_cycles])
    
    
    ## Combine arrays
    
    # Sample nrs, data, notes
    data = np.c_[sample_nrs, data_all_cycles, notes]
    
    # Add headers
    data = np.vstack([headers,data])
    

    return data, nsamples, nrepeat



# %% Function: generate rampdown data

"""
    Function to create stimulation data for rampdown routine.
    
    Input
    ----------
    flicker_freq : int
	Flicker frequency (40 Hz).
    
    max_analog : int
    Analog value corresponding to stim target illuminance (20 lux).
    
    sample_rate : int
    Frequency at which the Arduino reads CSV rows, in Hz.

    Output
    -------
    data : ndarray
	CSV file content below header.
    
    nsamples : int
	Nr of CSV rows containing output data.
    
    nrepeat : int
	Nr of times the CSV should be iterated over.

"""

def create_data_rampdown(flicker_freq,max_analog,sample_rate):

    ## Compute parameters

    # Duration of data file in sec
    data_file_time = 5
    
    # Nr. of samples for defined stim data duration
    nsamples = int(sample_rate * data_file_time)
    
    # Nr. of flicker cycles for defined stim data duration
    ncycles = flicker_freq * data_file_time

    # Nr. of repetitions (rampdown once)
    nrepeat = 1


    ## Required CSV format elements
    
    # Header row of data
    headers = ['Sample', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Channel5', 'Channel6', 'Trigger', 'Note']

    # Sample nrs
    sample_nrs = np.array([i for i in range(1, nsamples+1)])
    
    # Triggers (none)
    triggers = np.zeros((nsamples, 5))
    
    # Notes (none)
    notes = np.array([''] * nsamples)


    ## Generate cosine ramp
    
    # Array of radians between 0 (peak) & pi (trough), with nr. of elements = nr. of cycles
    radians = np.array([i for i in np.arange(0, np.pi, np.pi/(ncycles-0.5))]) # subtract 0.5 from ncycles to get correct nr of elements
    
    # Take cosine values of radians, with fitted amplitude & upward shift (for y in cosine shape)
    cosines = np.array([i for i in (max_analog/2) * np.cos(radians) + max_analog/2])
    
    # Round y values, as program only takes int values
    y_cos_int = np.round(cosines)
     
    
    ## Plot for visual inspection
    
    plt.figure()
    plt.plot(y_cos_int) # round for better comparison
    plt.title('Cosine ramp-down', size=30, y=1.05)
    plt.xlabel('Flicker cycles (0 - ' + str(data_file_time) + ' sec)', size=20)
    plt.ylabel('Analog values', size=20)


    ## Transform into data array with flicker
    
    # Initialize data array (2 channels)
    ramp_down = np.zeros((nsamples,2))
    
    # Fill cycles with ON period from cosines_int, leave OFF period at 0
    i = 0
    while i in range(0, ncycles):
        
        ramp_down[i*2] = y_cos_int[i]
        i += 1
    

    ## Combine arrays
    
    # Sample nrs, data, notes
    data = np.c_[sample_nrs, ramp_down, triggers, notes]
    
    # Add headers
    data = np.vstack([headers,data])


    return data, nsamples, nrepeat



# %% Function: write CSV

"""
    Function to write the full CSV file.
    
    Input
    ----------
    csv_nr : int
	Choose between CSV files 1,2,3.
    
    header : dict
    Output of create_header().
    
    data : np array
    Output of one create_data function.

    Output
    -------
    CSV file stored in directory.

"""

def write_CSV(csv_nr,header,data):
    
    # Defining mandatory filenames
    if csv_nr == 1:
        
        filename = 'rampup.csv'
        
    elif csv_nr == 2:
        
        filename = 'flicker.csv'
        
    elif csv_nr == 3:
        
        filename = 'rampdown.csv'
    
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')

        # Write header rows
        for key, value in header.items():
            writer.writerow([key, value, '', '', '', '', '', '', '', ''])

        # Write data rows
        for row in data:
            writer.writerow(row)



# %% Generate full CSV files

## Ramp-up

# Generate data
data_rampup, nsamples_rampup, nrepeat_rampup = create_data_rampup(flicker_freq,max_analog,sample_rate)

# Generate header
header_rampup = create_header(date,sample_rate,min_analog,max_analog,nsamples_rampup,nrepeat_rampup)

# Generate CSV
write_CSV(1,header_rampup,data_rampup)


## Flicker

# Generate data
data_flicker, nsamples_flicker, nrepeat_flicker = create_data_flicker(flicker_freq,max_analog,sample_rate)

# Generate header
header_flicker = create_header(date,sample_rate,min_analog,max_analog,nsamples_flicker,nrepeat_flicker)

# Generate CSV
write_CSV(2,header_flicker,data_flicker)


## Ramp-down

# Generate data
data_rampdown, nsamples_rampdown, nrepeat_rampdown = create_data_rampdown(flicker_freq,max_analog,sample_rate)

# Generate header
header_rampdown = create_header(date,sample_rate,min_analog,max_analog,nsamples_rampdown,nrepeat_rampdown)

# Generate CSV
write_CSV(3,header_rampdown,data_rampdown)





