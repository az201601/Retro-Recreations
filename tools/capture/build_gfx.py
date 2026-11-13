"""Extract the graphics for the spotlight intro + title screen from captured PPU state."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "capture", "work")
os.makedirs(WORK, exist_ok=True)
import pickle, numpy as np, os
from ppu import *
from PIL import Image
OUT=os.path.join(ROOT,'recreation','01_intro_title','assets')
os.makedirs(OUT+'/sprites',exist_ok=True); os.makedirs(OUT+'/backgrounds',exist_ok=True)
st=pickle.load(open(os.path.join(WORK,'st_idle.pkl'),'rb'))
def rgba(idx,alpha): 
    a=np.zeros(idx.shape+(4,),np.uint8); a[...,:3]=RGB[idx]; a[...,3]=np.where(alpha,255,0); a[~alpha]=0; return a
def strip(imgs,path):
    Image.fromarray(np.hstack(imgs)).save(path)
# ---- spotlight: 32 8x16 sprites -> one 64x63 image, 4 fade steps
def spot(p):
    pal=p['pal']&0x3f; img=np.zeros((63,64),np.uint8); al=np.zeros((63,64),bool)
    S=[sprite_img(p,i) for i in range(64)]; S=[s for s in S if s[1]<240]
    ox=min(s[0] for s in S); oy=min(s[1] for s in S)
    assert len(S)==32
    for x,y,at,im in reversed(S):
        c=pal[16+(at&3)*4+im]; m=im>0
        img[y-oy:y-oy+16,x-ox:x-ox+8][m]=c[m]; al[y-oy:y-oy+16,x-ox:x-ox+8]|=m
    return rgba(img,al)
spots=[spot(st[f]) for f in (300,)]
p=dict(st[300])
for f in (867,871,875):
    q=dict(st[300]); q['pal']=st[f]['pal']; spots.append(spot(q))
strip(spots,OUT+'/sprites/spr_spotlight_strip4.png')
for i,s in enumerate(spots): Image.fromarray(s).save(OUT+'/sprites/spr_spotlight_%d.png'%i)
# ---- BG masks (colour 1 = $0F black on every palette; drawn IN FRONT of the spotlight sprites)
for f,name in ((300,'bg_intro_wall'),(800,'bg_intro_silhouette')):
    pix,at=bg_layer(st[f]); idx=(st[f]['pal']&0x3f)[at*4+pix]
    assert set(np.unique(idx[pix>0]))=={0x0f}
    Image.fromarray(rgba(idx,pix>0)).save(OUT+'/backgrounds/%s.png'%name)
# ---- title: BG (+ behind-BG sprite 0) and front sprite layer, 4 fade steps
def title(p):
    v=p['vram'].copy(); v[:0x2000]=p['chrmid']; top=dict(p); top['vram']=v
    pal=p['pal']&0x3f
    out=np.full((240,256),pal[0],np.uint8); fg=np.zeros((240,256),np.uint8); fa=np.zeros((240,256),bool)
    for q,rows in ((top,slice(0,168)),(p,slice(168,240))):
        bgp,ba=bg_layer(q); o=np.where(bgp>0,pal[ba*4+bgp],pal[0])
        for i in range(63,-1,-1):
            x,y,at,im=sprite_img(q,i)
            if y>=240: continue
            for yy in range(im.shape[0]):
                for xx in range(8):
                    X=x+xx; Y=y+yy
                    if im[yy,xx] and Y<240 and 8<=X<256 and rows.start<=Y<rows.stop:
                        c=pal[16+(at&3)*4+im[yy,xx]]
                        if at&0x20:
                            if bgp[Y,X]==0: o[Y,X]=c
                        else: fg[Y,X]=c; fa[Y,X]=True
        out[rows]=o[rows]
    # NOTE: behind-BG sprites drawn before front ones is only correct if they do not overlap lower-index front sprites; verified by sim.
    return rgba(out,np.ones((240,256),bool)), rgba(fg,fa)
bgs=[];fgs=[]
for f in (892,896,900,904):
    b,g=title(st[f]); bgs.append(b); fgs.append(g)
strip(bgs,OUT+'/sprites/spr_title_bg_strip4.png'); strip(fgs,OUT+'/sprites/spr_title_fg_strip4.png')
for i in range(4):
    Image.fromarray(bgs[i]).save(OUT+'/sprites/spr_title_bg_%d.png'%i); Image.fromarray(fgs[i]).save(OUT+'/sprites/spr_title_fg_%d.png'%i)
print('ok')
