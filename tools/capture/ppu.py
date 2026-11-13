import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "capture", "work")
os.makedirs(WORK, exist_ok=True)
import numpy as np
PAL=[0x666666,0x002A88,0x1412A7,0x3B00A4,0x5C007E,0x6E0040,0x6C0600,0x561D00,0x333500,0x0B4800,0x005200,0x004F08,0x00404D,0,0,0,0xADADAD,0x155FD9,0x4240FF,0x7527FE,0xA01ACC,0xB71E7B,0xB53120,0x994E00,0x6B6D00,0x388700,0x0C9300,0x008F32,0x007C8D,0,0,0,0xFFFEFF,0x64B0FF,0x9290FF,0xC676FF,0xF36AFF,0xFE6ECC,0xFE8170,0xEA9E22,0xBCBE00,0x88D800,0x5CE430,0x45E082,0x48CDDE,0x4F4F4F,0,0,0xFFFEFF,0xC0DFFF,0xD3D2FF,0xE8C8FF,0xFBC2FF,0xFEC4EA,0xFECCC5,0xF7D8A5,0xE4E594,0xCFEF96,0xBDF4AB,0xB3F3CC,0xB5EBF2,0xB8B8B8,0,0]
RGB=np.array([[c>>16,(c>>8)&255,c&255] for c in PAL],np.uint8)
def tile(vram,addr):
    """8x8 array of 2-bit values for tile at CHR address"""
    p0=np.unpackbits(vram[addr:addr+8].reshape(8,1),axis=1); p1=np.unpackbits(vram[addr+8:addr+16].reshape(8,1),axis=1)
    return p0+2*p1
def bg_layer(p, nt=None):
    """returns 240x256 arrays: pix (0-3), attr(0-3) for the visible screen given scroll"""
    v=p['vram']; t=p['t']; base=0x1000 if p['ctrl']&0x10 else 0
    cx=t&31; cy=(t>>5)&31; fy=(t>>12)&7; n=(t>>10)&3; fx=p['x']
    sx=cx*8+fx+(n&1)*256; sy=cy*8+fy+(n>>1)*240
    full=np.zeros((480,512),np.uint8); fa=np.zeros((480,512),np.uint8)
    for q in range(4):
        b=0x2000+q*0x400; ox=(q&1)*256; oy=(q>>1)*240
        for r in range(30):
            for c in range(32):
                ti=int(v[b+r*32+c]); a=int(v[b+0x3C0+(r//4)*8+c//4]); sh=((r>>1)&1)*4+((c>>1)&1)*2
                full[oy+r*8:oy+r*8+8,ox+c*8:ox+c*8+8]=tile(v,base+ti*16)
                fa[oy+r*8:oy+r*8+8,ox+c*8:ox+c*8+8]=(a>>sh)&3
    ys=(np.arange(240)+sy)%480; xs=(np.arange(256)+sx)%512
    return full[np.ix_(ys,xs)], fa[np.ix_(ys,xs)]
def sprite_img(p,i):
    v=p['vram']; y,tl,at,x=[int(k) for k in p['oam'][i*4:i*4+4]]
    if p['ctrl']&0x20:
        b=(tl&1)*0x1000+(tl&0xFE)*16
        im=np.vstack([tile(v,b),tile(v,b+16)])
    else:
        im=tile(v,(0x1000 if p['ctrl']&8 else 0)+tl*16)
    if at&0x40: im=im[:,::-1]
    if at&0x80: im=im[::-1]
    return x,y+1,at,im
def render(p):
    pal=p['pal']&0x3f; mask=p['mask']
    out=np.full((240,256),pal[0],np.uint8)
    bgp=np.zeros((240,256),np.uint8)
    if mask&8:
        bgp,ba=bg_layer(p)
        if not mask&2: bgp[:,:8]=0
        c=pal[(ba*4+bgp)]; out=np.where(bgp>0,c,out)
    if mask&0x10:
        spr_pix=np.zeros((240,256),np.uint8); spr_at=np.zeros((240,256),np.uint8)
        for i in range(63,-1,-1):
            x,y,at,im=sprite_img(p,i)
            if y>=240: continue
            h,w=im.shape
            for yy in range(h):
                for xx in range(w):
                    if im[yy,xx] and y+yy<240 and x+xx<256:
                        spr_pix[y+yy,x+xx]=im[yy,xx]; spr_at[y+yy,x+xx]=at
        if not mask&4: spr_pix[:,:8]=0
        sc=pal[16+(spr_at&3)*4+spr_pix]
        show=(spr_pix>0)&((bgp==0)|((spr_at&0x20)==0))
        out=np.where(show,sc,out)
    return RGB[out]
def render_split(p):
    L=p['lines']; ch=[i for i in range(1,240) if not np.array_equal(L[i,5:],L[i-1,5:])]
    if not ch: return render(p)
    s=ch[0]; q=dict(p); v=p['vram'].copy(); v[:0x2000]=p['chrmid']; q['vram']=v
    a=render(q); b=render(p); a[s:]=b[s:]; return a
