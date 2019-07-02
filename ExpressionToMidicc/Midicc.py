import numpy as np
from mido import Message
import scipy as sp

class SynthesisToMidicc:
    
    def __init__(self, vibind, bpm, extent_crest, extent_trough):
        
        self.vibind = vibind
        self.extent_crest = extent_crest
        self.extent_trough = extent_trough
        self.start_vib_tick = None
        self.microsec_per_tick = ((60 / bpm)/480) * 1000
        self.vib_tick = None
        self.speed = None
        self.tune = None
        self.Onset_absoluted = None
        self.Offset_absoluted = None
        self.Onset_related = None
        self.Offset_related = None
        self.H_ve_max = 42.2700 # h_a_vib{1,1}{2,3}(19)
        self.H_ve_min = -44.8894 # h_a_vib{1,1}{3,3}(16)
        self.O_ve_max = 56.2959 # o_a_vib{1,1}{4,5}(1)
        self.O_ve_min = -77.2698 # o_na_vib{1,1}{7,5}(3)
        self.H_diff = self.H_ve_max - self.H_ve_min
        self.O_diff = self.O_ve_max - self.O_ve_min
        self.extent_max = self.extent_crest[126][1]
        self.extent_min = self.extent_trough[0][1]
        self.midi_diff = self.extent_max - self.extent_min
        self.H_scale = self.midi_diff / self.H_diff
        self.O_scale = self.midi_diff / self.O_diff
        
    def eCToExpression(self, miditrack, ec, noteindex, vib_flag):
        '''interporlation energy contour : 150 -> 150 * the tick of offset'''
        y = ec
        x = np.arange(y.size)
        ec_new_x = np.linspace(x.min(),x.max(),len(ec)*self.Offset_related[noteindex])
        ec_new_y = sp.interpolate.interp1d(x,y.reshape(len(ec)),kind='linear')(ec_new_x)
        ec_new_y = 128 * ec_new_y # energy contour map to expression value
        ec_int = ec_new_y.astype(int) # energy contour: float to int
        ec_final = ec_int[::len(ec)]

        speed_idx = 0
        for i in range(self.Offset_related[noteindex]):
            miditrack.append(Message('control_change', channel = 0, control = 11, value = ec_final[i], time = 1))
            if(vib_flag == True):
                if(i in self.vib_tick):
                    if(speed_idx != (len(self.vib_tick)-1)):
                        miditrack.append(Message('control_change', channel = 0, control = 1, value = 127, time = 0))
                        miditrack.append(Message('control_change', channel = 0, control = 65, value = self.speed[speed_idx][0], time = 0))
                        miditrack.append(Message('control_change', channel = 0, control = 67, value = self.tune[speed_idx], time = 0))
                        speed_idx += 1
                    else:
                        miditrack.append(Message('control_change', channel = 0, control = 1, value = 0, time = 0))
                if(i == self.Offset_related[noteindex] - 1):
                    miditrack.append(Message('control_change', channel = 0, control = 1, value = 0, time = 0))
        self.Offset_related[noteindex] = 0

    def vibratoMaptoMidi(self, miditrack, vr, ve, noteIndex):
        '''calculate the tick of VR and VE'''
        self.start_vib_tick = (np.around(self.Offset_absoluted[noteIndex] * 0.2)).astype(int)
        #vr_tick = np.around(vr)
        vr_tick = 1 / vr
        vr_tick[0] *= 0.25
        vr_tick[1::] *= 0.5
        vr_tick *= 1000
        vr_tick /= self.microsec_per_tick
        vr_tick = np.ceil(vr_tick)
        vr_tick = vr_tick.astype(int)
        self.vib_tick = vr_tick
        self.vib_tick = np.insert(self.vib_tick, 0, self.start_vib_tick)
        self.vib_tick = np.cumsum(self.vib_tick)
        
        '''calculate vibrato rate to speed'''
        speed = (np.around(((((vr/2)-1.12)/0.0315) + 4))).astype(int)
        speed[speed > 127] = 127
        self.speed = speed
        '''calculate vibrato extent to tune'''
        ve[1:-1:2] *= -1
        ve_cumsum = np.cumsum(ve)
        ve_final = np.around(ve_cumsum)
        
        ve_crest = ve_final[0::2] 
        ve_trough = ve_final[1::2] 
        ve_crest[ve_crest > 9.4240] = 9.4240
        ve_trough[ve_trough < -18.1145] = -18.1145
        
        tune_crest = np.empty(len(ve_crest))
        for i in range(len(ve_crest)):
            if ve_crest[i] < 9.4240 and ve_crest[i] > 8.5892:
                tune_crest[i] = 119
            elif ve_crest[i] < 8.5892 and ve_crest[i] > 7.7983:
                tune_crest[i] = 103
            elif ve_crest[i] < 7.7983 and ve_crest[i] > 7.0245:
                tune_crest[i] = 88
            elif ve_crest[i] < 7.0245 and ve_crest[i] > 6.1886:
                tune_crest[i] = 72
            elif ve_crest[i] < 6.1886 and ve_crest[i] > 5.4366:
                tune_crest[i] = 56
            elif ve_crest[i] < 5.4366 and ve_crest[i] > 4.5942:
                tune_crest[i] = 40
            elif ve_crest[i] < 4.5942 and ve_crest[i] > 4.1235:
                tune_crest[i] = 24
            elif tune_crest[i] < 4.1235:
                tune_crest[i] = 16
            else:
                tune_crest[i] = 127
        tune_trough = np.empty(len(ve_trough))
        for i in range(len(ve_trough)):
            if ve_trough[i] < -15.9905 and ve_trough[i] > -18.1145:
                tune_trough[i] = 119
            elif ve_trough[i] < -14.0353 and ve_trough[i] > -15.9905:
                tune_trough[i] = 103
            elif ve_trough[i] < -12.0766 and ve_trough[i] > -14.0353:
                tune_trough[i] = 88
            elif ve_trough[i] < -9.9948 and ve_trough[i] > -12.0766:
                tune_trough[i] = 72
            elif ve_trough[i] < -7.9975 and ve_trough[i] > -9.9945:
                tune_trough[i] = 56
            elif ve_trough[i] < -5.8604 and ve_trough[i] > -7.9975:
                tune_trough[i] = 40
            elif ve_trough[i] < -4.1841 and ve_trough[i] > -5.8604:
                tune_trough[i] = 24
            elif ve_trough[i] > -4.1841:
                tune_trough[i] = 16
            else:
                tune_trough[i] = 127
                
        tune = np.empty(len(ve))
        tune[0::2] = tune_crest
        tune[1::2] = tune_trough
        self.tune = tune.astype(int)
        '''calculate vibrato extent to tune'''
        ve[1::2] *= -1
        ve_cumsum = np.cumsum(ve)
        ve_crest = ve_cumsum[0::2] 
        ve_trough = ve_cumsum[1::2]
        #ve_crest[ve_crest > self.extent_max] = self.extent_max
        #ve_trough[ve_trough < self.extent_mve_crest[i]n] = self.extent_min
        ve_crest[ve_crest > self.extent_max] = self.extent_max
        ve_trough[ve_trough < self.extent_min] = self.extent_min
        tune_trough = []
        tune_crest = []
        min_ve = 10000
        for v in range(len(ve_crest)):
            for d in self.extent_crest:
                temp = abs(ve_crest[v] - d[1])
                if temp < min_ve:
                    min_ve = min(temp, min_ve)
                    extent_value = d[0]
            min_ve = 10000       
            tune_crest.append(extent_value)
        min_ve = 10000   
        for v in range(len(ve_trough)):
            for d in self.extent_trough:
                temp = abs(ve_trough[v] - d[1])
                if temp < min_ve:
                    min_ve = min(temp, min_ve)
                    extent_value = d[0]
            min_ve = 10000       
            tune_trough.append(extent_value)
        tune = np.empty(len(ve))
        tune[0::2] = tune_crest
        tune[1::2] = tune_trough
        self.tune = tune.astype(int)
        
        return speed,tune
    
    def calOnsetOffset(self, bpm, dur, kot):
        Onset_t = np.empty(len(dur))
        Offset_t = np.empty(len(dur))
        release = 107
        release_long = 200
#        scale = 1.19
#        dur *= scale
        dur = dur / 1.2
        #dur = dur/1.2*139/120
        '''calculate absolute time of onset and offset.'''
        for i in range(len(dur)):
            if(i == 0):
                Onset_t[i] = 0
                Offset_t[i] = dur[0] - release
            else:
                Onset_t[i] = Onset_t[i-1] + dur[i-1] - kot[i-1]
                if (i == 26 or i == 36):
                    Offset_t[i] = Onset_t[i] + dur[i]
                else:
                    Offset_t[i] = Onset_t[i] + dur[i] - release
                    if(Onset_t[i] < Offset_t[i-1]):
                        Offset_t[i-1] = Onset_t[i-1] + dur[i-1] - release_long

        '''calculate onset and offset to tick unit.'''
        Onset = np.around(Onset_t / self.microsec_per_tick)
        Offset = np.around(Offset_t / self.microsec_per_tick)
            
        '''calculate related time of onset and offset.'''
        Onset_tick = np.zeros(len(Onset))
        Offset_tick = np.zeros(len(Offset))
        
        for c in range(len(Onset)):
            if(c == 0):
                Onset_tick[c] = Onset[0]
                Offset_tick[c] = Offset[0]
            else:
                Onset_tick[c] = Onset[c] - Offset[c-1]
                Offset_tick[c] = Offset[c] - Onset[c]
       
        '''float to int. '''
        Onset_final = Onset_tick.astype(int)
        Offset_final = Offset_tick.astype(int)
            
        self.Onset_related = Onset_final
        self.Offset_related = Offset_final
        self.Onset_absoluted = Onset_tick.astype(int)
        self.Offset_absoluted = Offset_tick.astype(int)  