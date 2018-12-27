import scipy.io as scio
import numpy as np
from mido import Message, MidiFile, MidiTrack
import ExpressionToMidicc.Midicc as midi

Expression = scio.loadmat('H_synthesis_parameter.mat')
MidiNum = scio.loadmat('midi')

MidiNote = np.array(MidiNum['midi']) # midi notenumber
VibInd_temp = np.array(Expression['H_synthesis_parameter']['VibInd'])[0][0] # note vibrato index
VibInd = (VibInd_temp-np.ones(len(VibInd_temp))).astype(int) # matlab to python, index need to minus 1
DUR = np.array(Expression['H_synthesis_parameter']['DUR'])[0][0] # note duration
EC = np.array(Expression['H_synthesis_parameter']['EC'])[0][0][0] # note energycontour
VRVC = np.array(Expression['H_synthesis_parameter']['VRVC'])[0][0][0] # note vibrato rate
VEVC = np.array(Expression['H_synthesis_parameter']['VEVC'])[0][0][0] # note vibrato extent
KOT = np.array(Expression['H_synthesis_parameter']['KOT'])[0][0] # note kot
BPM = 92

outfile = MidiFile()
track = MidiTrack()
outfile.tracks.append(track)

s = midi.SynthesisToMidicc(VibInd, BPM)

track.append(Message('program_change', program = 40)) # timbre => violin
track.append(Message('note_on', note = 25, velocity = 127, time = 0)) # sustain effect
track.append(Message('control_change', channel = 0, control = 6, value = 127, time = 0 )) # ks-key
track.append(Message('control_change', channel = 0, control = 32, value = 127, time = 0 )) # x-fade
track.append(Message('control_change', channel = 0, control = 42, value = 0, time = 0 )) # room
track.append(Message('control_change', channel = 0, control = 46, value = 0, time = 0 )) # body
track.append(Message('control_change', channel = 0, control = 51, value = 0, time = 0 )) # artificial legato
track.append(Message('control_change', channel = 0, control = 58, value = 0, time = 0 )) # legato short
track.append(Message('control_change', channel = 0, control = 54, value = 0, time = 0 )) # legato long

s.calOnsetOffset(BPM, DUR, KOT) # calculate onset and offset

VibCount = 0
VibFlag = False
for notenum in range(len(MidiNote)): 
    track.append(Message('note_on', note = MidiNote[notenum][0], velocity = 127, time = s.Onset_related[notenum]))
    if(notenum in VibInd):
        VibFlag = True
        speed , tune = s.vibratoMaptoMidi(track, VRVC[VibCount], VEVC[VibCount], notenum)
        VibCount += 1
    s.eCToExpression(track, EC[notenum], notenum, VibFlag)
    VibFlag = False
    track.append(Message('note_off', note = MidiNote[notenum][0], velocity = 127, time = s.Offset_related[notenum]))
outfile.save('final.mid')   