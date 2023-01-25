# -*- coding: utf-8 -*-
"""
Function to get photodiode triggers using a trigger template & create 40 equal segments per second

"""


# =============================================================================
# Inputs:
#   - rawdata: output from load_data

# Output:
#   - triggers: indices of data points that are triggers 
# =============================================================================


### Libraries
import numpy as np


def get_triggers(rawdata):

    # Load photodiode & EOG channels
    photo_diode_data = rawdata[7]
    EOG_data = rawdata[6] 
    
    # Subtract to get just the triggers
    trigger_data = photo_diode_data - EOG_data 
    
    # Baseline correct
    trigger_data = trigger_data - trigger_data.mean() 
    
    # Get differential
    diff_trigger_data = np.diff(trigger_data)
    
    # If the channels were the wrong way, it might be necessary to flip the data
    trigger_data = trigger_data * -1 
    
    triggers = [] # empty list to put triggers into
        
    trigger_count = 0 # counter to keep track of the number of triggers
        
    trigger_time_series = np.zeros([len(trigger_data,)]) # a time series to mark the locations of the triggers, to check the timing is correct
    
    print(' ')
    print('Searching for triggers ...')
        
    k = 15 # change here if to start later
    
    while k < len(trigger_data) - 10:         
        
        if diff_trigger_data[k] > 200: # if the first differential of the trigger data is above a certain threshold, indicating a steep rising edge
        
            trigger_time = np.argmax(diff_trigger_data[k-10:k+10]) + k + 11# check for the max value in the +/- 10 data points, to be sure the trigger is the peak
            
            triggers.append(trigger_time) # add to list of triggers
            
            trigger_count += 1 # count number of triggers            
                
            k = k + 10 # skip forward data points, so not to include the same trigger twice
        
        k += 1 # move forward one
            
    
    ## only include triggers that are one second apart, and for each one second trigger make 40 separate triggers
    
    triggers_list = np.array(triggers)
    
    good_triggers_list = []
        
    k = 0
    
    while k < len(triggers_list)-1:
        
        if np.abs((triggers_list[k+1] - triggers_list[k]) - 1000)<= 2:
            
            relative_trigger_time = 0 # the time of the 40 Hz flicker relative to the trigger
            
            for t in range(0,40):
            
                trigger_time = triggers_list[k]+relative_trigger_time
                good_triggers_list.append(trigger_time)
                trigger_time_series[trigger_time] = 200
                
                relative_trigger_time = relative_trigger_time + 25
                
        k+=1
        
    
    print(str(len(good_triggers_list)) + ' triggers included (max. 12000)')
     
    # convert to numpy array
    good_triggers_list = np.array(good_triggers_list, dtype=int)
     
    # convert to numpy array
    triggers_np = np.array(good_triggers_list, dtype=int)
        
    return triggers_np
             
    
