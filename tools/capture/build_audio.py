"""Cut the 4 audio pieces out of the emulator captures and retime them from the NES frame rate
(60.0988 fps) to exactly 800 samples per frame @48 kHz, so that 1 GMS step (room_speed 60) == 1 NES frame."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "capture", "work")
os.makedirs(WORK, exist_ok=True)
import numpy as np, soxr, soundfile as sf, os
OUT=os.path.join(ROOT,'recreation','01_intro_title','assets','sounds'); os.makedirs(OUT,exist_ok=True)
nat=np.load(WORK+'/aud_long.npy')[:,0].astype(np.float64)/32768; cn=np.load(WORK+'/cnt_long.npy')
skp=np.load(WORK+'/audL_skip300.npy').astype(np.float64)/32768; cs=np.load(WORK+'/cntL_skip300.npy')
def piece(a,c,f0,n,name,fade_out=0):
    x=a[c[f0-1]:c[f0+n-1]]; N=n*800
    y=soxr.resample(x,len(x)*60.0/n,48000,quality='VHQ')
    y=y[:N] if len(y)>=N else np.concatenate([y,np.zeros(N-len(y))])
    if fade_out: y[-fade_out:]*=np.linspace(1,0,fade_out)
    with sf.SoundFile('%s/%s.ogg'%(OUT,name),'w',samplerate=48000,channels=1,format='OGG',subtype='VORBIS') as f:
        for i in range(0,len(y),2048): f.write(y[i:i+2048].astype(np.float32))
    chk,sr=sf.read('%s/%s.ogg'%(OUT,name))
    print(name,'frames',n,'in',len(x),'out',len(y),'ogg samples',len(chk),sr,'peak %.3f'%np.abs(y).max(),'ends',np.abs(y[:50]).max().round(4),np.abs(y[-50:]).max().round(4), os.path.getsize('%s/%s.ogg'%(OUT,name)))
piece(nat,cn,156,44,'snd_intro_pops')
piece(nat,cn,653,150,'snd_intro_jingle')
piece(nat,cn,803,85,'snd_intro_roll',fade_out=96)
piece(skp,cs,326,2880,'snd_title_theme')
