import scipy.io as scio
import numpy as np
from mido import Message, MidiFile, MidiTrack
import ExpressionToMidicc.Midicc as midi

Expression = scio.loadmat('midiparameter\h_parameter_spring.mat')
MidiNum = scio.loadmat('midiparameter\h_parameter_spring_midi')
ExtentDict = scio.loadmat('ExtentDict.mat')

s = 'h_spring'
MidiNote = np.array(MidiNum['midi']) # midi notenumber
VibInd_temp = np.array(Expression[s]['VibInd'])[0][0] # note vibrato index
VibInd = (VibInd_temp-np.ones(len(VibInd_temp))).astype(int) # matlab to python, index need to minus 1
DUR = np.array(Expression[s]['DUR'])[0][0] # note duration
DUR = DUR.astype(float)
EC = np.array(Expression[s]['EC'])[0][0][0] # note energycontour
VRVC = np.array(Expression[s]['VRVC'])[0][0][0] # note vibrato rate
VEVC = np.array(Expression[s]['VEVC'])[0][0][0] # note vibrato extent
KOT = np.array(Expression[s]['KOT'])[0][0] # note kot
staccato_spring = [51, 52 ,55 ,56]
staccato_bach = [131,132,133,134]
BPM = 143

Extent_crest = {}
Extent_trough = {}
for i in range(127):
    Filename = np.array(ExtentDict['VE_struct_final'])[i][0][0][0][0:-4]
    Filename = Filename[3::]
    Crest = np.array(ExtentDict['VE_struct_final'])[i][0][6][0][0]
    Trough = np.array(ExtentDict['VE_struct_final'])[i][0][7][0][0]
    Extent_crest.update({Filename:Crest})
    Extent_trough.update({Filename:Trough})
Extent_crest = sorted(Extent_crest.items(),key = lambda item:item[1]) 
Extent_trough = sorted(Extent_trough.items(),key = lambda item:item[1])

outfile = MidiFile()
track = MidiTrack()
outfile.tracks.append(track)

s = midi.SynthesisToMidicc(VibInd, BPM, Extent_crest, Extent_trough)

track.append(Message('program_change', program = 40)) # timbre => violin
track.append(Message('note_on', note = 25, velocity = 127, time = 0)) # sustain effect
track.append(Message('control_change', channel = 0, control = 6, value = 127, time = 0 )) # ks-key
track.append(Message('control_change', channel = 0, control = 32, value = 127, time = 0 )) # x-fade
track.append(Message('control_change', channel = 0, control = 42, value = 0, time = 0 )) # room
track.append(Message('control_change', channel = 0, control = 46, value = 0, time = 0 )) # body
track.append(Message('control_change', channel = 0, control = 51, value = 0, time = 0 )) # artificial legato
track.append(Message('control_change', channel = 0, control = 58, value = 0, time = 0 )) # legato short
track.append(Message('control_change', channel = 0, control = 54, value = 0, time = 0 )) # legato long

track.append(Message('program_change', channel = 1, program = 40)) # timbre => violin
track.append(Message('note_on', channel = 1, note = 34, velocity = 127, time = 0))
track.append(Message('control_change', channel = 1, control = 6, value = 127, time = 0 )) # ks-key
track.append(Message('control_change', channel = 1, control = 32, value = 127, time = 0 )) # x-fade
track.append(Message('control_change', channel = 1, control = 42, value = 0, time = 0 )) # room
track.append(Message('control_change', channel = 1, control = 46, value = 0, time = 0 )) # body
track.append(Message('control_change', channel = 1, control = 51, value = 0, time = 0 )) # artificial legato
track.append(Message('control_change', channel = 1, control = 58, value = 0, time = 0 )) # legato short
track.append(Message('control_change', channel = 1, control = 54, value = 0, time = 0 )) # legato long
s.calOnsetOffset(BPM, DUR, KOT) # calculate onset and offset

VibCount = 0
VibFlag = False
#for notenum in range(len(MidiNote)): 
#    track.append(Message('note_on', note = MidiNote[notenum][0], velocity = 127, time = s.Onset_related[notenum]))
#    if(notenum in VibInd):
#        VibFlag = True
#        s.vibratoMaptoMidi(track, VRVC[VibCount], VEVC[VibCount], notenum)
#        VibCount += 1
#    s.eCToExpression(track, EC[notenum][0], notenum, VibFlag)
#    VibFlag = False
#    track.append(Message('note_off', note = MidiNote[notenum][0], velocity = 127, time = s.Offset_related[notenum]))
channel_num = 1
for notenum in range(len(MidiNote)): 
    if(notenum in staccato_spring):
        track.append(Message('note_on', channel = channel_num,note = MidiNote[notenum][0], velocity = 64, time = s.Onset_related[notenum]))
        track.append(Message('note_off', channel = channel_num, note = 25, velocity = 0, time = 0)) # sustain effect
        track.append(Message('note_on', channel = channel_num, note = 34, velocity = 127, time = 0)) 
        track.append(Message('control_change', channel = channel_num, control = 31, value = 0, time = 0 ))
        track.append(Message('note_off', channel = channel_num, note = MidiNote[notenum][0], velocity = 64, time = s.Offset_related[notenum]))
    else:
        track.append(Message('note_on', note = MidiNote[notenum][0], velocity = 127, time = s.Onset_related[notenum]))
        track.append(Message('control_change', channel = 0, control = 32, value = 127 , time = 0 ))
        #track.append(Message('control_change', channel = 0, control = 116, value = 0, time = 0 ))
        if(notenum in VibInd):
            VibFlag = True
            s.vibratoMaptoMidi(track, VRVC[VibCount], VEVC[VibCount], notenum)
            VibCount += 1
        s.eCToExpression(track, EC[notenum][0], notenum, VibFlag)
        VibFlag = False
        track.append(Message('note_off', note = MidiNote[notenum][0], velocity = 127, time = s.Offset_related[notenum])) 

outfile.save('midiparameter\H_spring_twoChannel.mid')