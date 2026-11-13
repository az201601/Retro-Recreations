"""Python port of the GML in obj_intro (Create/Step/Draw), used to verify the logic + exported PNGs
pixel-for-pixel against the emulator. Keep in sync with recreation/01_intro_title/gml/*.gml"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "capture", "work")
os.makedirs(WORK, exist_ok=True)
import numpy as np, math
from PIL import Image
A=os.path.join(ROOT,'recreation','01_intro_title','assets')+'/'
ld=lambda p: np.array(Image.open(A+p).convert('RGBA'))
SPOT=[ld('sprites/spr_spotlight_%d.png'%i) for i in range(4)]
TBG=[ld('sprites/spr_title_bg_%d.png'%i) for i in range(4)]
TFG=[ld('sprites/spr_title_fg_%d.png'%i) for i in range(4)]
WALL=ld('backgrounds/bg_intro_wall.png'); SIL=ld('backgrounds/bg_intro_silhouette.png')
EMU0=156
class Intro:
    def __init__(s):   # Create
        s.frame=-1; s.skip_frame=-1; s.fade_start=711
        s.spot_on=False; s.spot_x=0; s.spot_y=0; s.spot_vx=0; s.spot_vy=0; s.spot_fade=0
        s.bg_mode=0; s.title_fade=-1; s.accept_start=False; s.menu=False
        s.snd_queue=None; s.sounds=[]
    def step(s,start_pressed):   # Step
        s.frame+=1; n=s.frame
        if s.snd_queue is not None:
            s.sounds.append((n,s.snd_queue)); s.snd_queue=None
        if n==0: s.sounds.append((n,'pops'))
        if s.skip_frame<0 and n<s.fade_start:      # scripted part (frozen once START skipped it)
            if n==14: s.bg_mode=1
            elif n==32: s.spot_on=True; s.spot_x=160*256; s.spot_y=-95*256; s.spot_vx=0; s.spot_vy=512
            elif n==160: s.spot_vx=-352; s.spot_vy=-352
            elif n==256: s.spot_vx=512; s.spot_vy=0
            elif n==320: s.spot_vx=-352; s.spot_vy=352
            elif n==368: s.spot_vx=-512; s.spot_vy=0
            elif n==496: s.bg_mode=2; s.snd_queue='jingle'
            elif n==497: s.spot_x=-164*256; s.spot_y=73*256; s.spot_vx=512
            elif n==630: s.spot_vx=-1024
            elif n==646: s.spot_vx=0; s.snd_queue='roll'
            if s.spot_on: s.spot_x+=s.spot_vx; s.spot_y+=s.spot_vy
            if start_pressed and 32<=n<=645:
                s.skip_frame=n; s.fade_start=n+5
        f=n-s.fade_start
        if f>=0:
            if f==0: s.spot_fade=1
            elif f==4: s.spot_fade=2
            elif f==8: s.spot_fade=3
            elif f==12: s.spot_on=False
            elif f==17: s.bg_mode=0
            elif f==20: s.snd_queue='theme'
            elif f==25: s.title_fade=0
            elif f==29: s.title_fade=1
            elif f==33: s.title_fade=2
            elif f==37: s.title_fade=3
            if f>=38 and start_pressed and not s.menu: s.menu=True
    def draw(s):
        scr=np.zeros((240,256,3),np.uint8)
        def blit(img,sx,sy,w,h,dx,dy):
            if w<=0 or h<=0: return
            src=img[sy:sy+h,sx:sx+w]
            x0=max(dx,0);y0=max(dy,0);x1=min(dx+w,256);y1=min(dy+h,240)
            if x1<=x0 or y1<=y0: return
            src=src[y0-dy:y1-dy,x0-dx:x1-dx]; m=src[...,3]>0
            scr[y0:y1,x0:x1][m]=src[...,:3][m]
        if s.spot_on:
            ox=math.floor(s.spot_x/256); oy=math.floor(s.spot_y/256)
            left=max(0,8-ox)
            if oy>=1: top=0
            elif oy+16>=1: top=16
            elif oy+31>=1: top=31
            elif oy+47>=1: top=47
            else: top=-1
            if top>=0 and left<64: blit(SPOT[s.spot_fade],left,top,64-left,63-top,ox+left,oy+top)
        if s.bg_mode==1: blit(WALL,0,0,256,240,0,0)
        elif s.bg_mode==2: blit(SIL,0,0,256,240,0,0)
        if s.title_fade>=0:
            blit(TBG[s.title_fade],0,0,256,240,0,0); blit(TFG[s.title_fade],0,0,256,240,0,0)
        return scr
def run(nframes,press=()):
    g=Intro(); out=[]
    for n in range(nframes):
        g.step(n+EMU0 in press); out.append(g.draw())
    return out,g
if __name__=='__main__':
    fr=np.load(WORK+'/frames_idle.npy',mmap_mode='r')
    out,g=run(1199-EMU0)
    bad=[n+EMU0 for n in range(len(out)) if not np.array_equal(out[n],fr[n+EMU0])]
    print('natural: frames compared',len(out),'mismatches',len(bad),bad[:20]); print(g.sounds)
    for t in (187,188,235,300,410,474,568,650,652,653,700,706,784,800,801,802):
        ref=np.load(WORK+'/fr_skip%d.npy'%t,mmap_mode='r')   # frames t-2 .. t+397
        out,g=run(t+398-EMU0,press=(t,))
        bad=[k+t-2 for k in range(400) if not np.array_equal(out[k+t-2-EMU0],ref[k])]
        print('START on NES frame',t,'-> mismatches',len(bad),bad[:10],'skipped' if g.skip_frame>=0 else 'ignored',g.sounds)
