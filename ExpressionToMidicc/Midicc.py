import numpy as np
from mido import Message
import scipy as sp

class SynthesisToMidicc:
    
    def __init__(self, vibind, bpm):
        
        self.vibind = vibind
        self.start_vib_tick = None
        self.microsec_per_tick = ((60 / bpm)/480) * 1000
        self.vib_tick = None
        self.speed = None
        self.tune = None
        self.Onset_absoluted = None
        self.Offset_absoluted = None
        self.Onset_related = None
        self.Offset_related = None
        
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
                        miditrack.append(Message('control_change', channel = 0, control = 67, value = self.tune[speed_idx ], time = 0))
                        speed_idx += 1
                    else:
                        miditrack.append(Message('control_change', channel = 0, control = 1, value = 0, time = 0))
                    
        self.Offset_related[noteindex] = 0

    def vibratoMaptoMidi(self, miditrack, vr, ve, noteIndex):
        '''calculate the tick of VR and VE'''
        self.start_vib_tick = (np.around(self.Offset_absoluted[noteIndex] * 0.2)).astype(int)
        vr_tick = np.around(vr)
        vr_tick = 1 / vr_tick
        vr_tick[::] *= 0.25
        vr_tick *= 1000
        vr_tick /= self.microsec_per_tick
        vr_tick = vr_tick.astype(int)
        self.vib_tick = vr_tick + 25
        self.vib_tick = np.insert(self.vib_tick, 0, self.start_vib_tick)
        self.vib_tick = np.cumsum(self.vib_tick)
        
        '''calculate vibrato rate to speed'''
        speed = (np.around(((((vr/2)-1.12)/0.0315) + 4))).astype(int)
        speed[speed > 127] = 127
        self.speed = speed
        
        '''calculate vibrato extent to tune'''
        ve[1:-1:2] *= -1
        ve_cumsum = np.cumsum(ve)
        ve_abs = np.abs(ve_cumsum)
        ve_final = np.around(ve_abs)
        
        ve_trough = ve_final[0::2] #波谷
        ve_crest = ve_final[1::2] #波峰
        ve_crest_max = ve_crest.max()
        ve_crest[ve_crest_max > 10] = ve_crest - (ve_crest_max - 10)
        ve_crest[ve_crest < 4] = 4
        ve_crest = ve_crest.astype(int)
        diff = ve_crest_max - 10
        ve_trough[ve_crest_max > 10] = ve_trough + diff
        ve_trough[ve_trough > 56 ] = 56
        ve_trough[ve_trough < 44] = 44
        ve_trough = ve_trough.astype(int)
        tune_crest = 127 - ((10 - ve_crest) * 8)
        tune_trough = (8 * (ve_trough - 44)) + 31
        tune = np.empty(len(ve))
        tune[0::2] = tune_trough
        tune[1::2] = tune_crest
        self.tune = tune.astype(int)
        
        return speed,tune
    def calOnsetOffset(self, bpm, dur, kot):
        Onset_t = np.empty(len(dur))
        Offset_t = np.empty(len(dur))
        release = 107
        release_long = 200
        dur = dur / 1.2
        
        '''calculate absolute time of onset and offset.'''
        for i in range(len(dur)):
            if(i == 0):
                Onset_t[i] = 0
                Offset_t[i] = dur[0] - release
            else:   
                Onset_t[i] = Onset_t[i-1] + dur[i-1] - kot[i-1]
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