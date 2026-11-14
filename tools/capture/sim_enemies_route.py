#!/usr/bin/env python3
"""A second check of the enemies of deliverable 9: the port of sim_enemies.py against the three route recordings of
capture_level1.py (the whole section walked through, NES frames 1700-3700, all twelve objects).  The route's player
gets hurt, which the port does not do yet, so the player's position and body height and the camera are taken from
the NES memory on every frame; only the enemies are the port's.  Compared per place in the object list: position
with fractions, speeds, picture, direction, hit points, damage, body size.  Frames the NES left out are skipped.
usage: sim_enemies_route.py"""
import sys
import sim_enemies as S, capture_level1 as L
from scenario import load
PADBIT=S.PADBIT
class Foreign: pass
def run(names, verbose=8):
    g=S.Stage(); pad=lambda f: sum(PADBIT[k] for k in L.ROUTE.get(f, []))
    cur={'p2d':-1}; lags=[]
    def hook(g):
        r=cur['r']; g.pl.p_x=int(r[0x314]); g.pl.p_y=int(r[0x2FC]); g.pl.p_h=int(r[0x3BC]); g.lv_cam_x=int(r[0x10])+256*int(r[0x13])
        for j in range(3,12):
            fo=(int(r[0x2F0+j])&0x0F)==1 and r[0x32C+j]==0
            if fo and g.lv_slot[j] is None: g.lv_slot[j]=Foreign()
            if not fo and isinstance(g.lv_slot[j],Foreign): g.lv_slot[j]=None
    f=1357; bad=0; n=0
    for nm in names:
        d=load(nm); f0=d['f0']
        while f<f0: g.end_step(pad(f)); f+=1
        g.follow=hook
        for S_ in d['st']:
            r=S_['ram']; cur['r']=r
            if f>3700: break
            if f>f0 and r[0x2D]==cur['p2d']: cur['p2d']=r[0x2D]; f+=1; lags.append(f-1); continue      # the NES dropped a frame
            cur['p2d']=r[0x2D]
            g.end_step(pad(f)); cam=int(r[0x10])+256*int(r[0x13]); n+=1
            nes={}; sim={}
            for j in range(3,12):
                kd=int(r[0x2F0+j])&0x0F
                if kd in (6,8) and r[0x32C+j]==7 or (kd in (6,8) and r[0x2F0+j]&0x80):
                    x=int(r[0x314+j])+256*int(r[0x320+j]); x=x-65536 if x>32767 else x
                    y=int(r[0x2FC+j])+256*int(r[0x308+j]); y=y-65536 if y>32767 else y
                    sg=lambda v:int(v)-256 if v>127 else int(v)
                    if r[0x2F0+j]&0x80: nes[j]=(x+cam,y)
                    else: nes[j]=(x+cam,y,int(r[0x368+j])>>4,int(r[0x374+j])>>4,sg(r[0x350+j]),sg(r[0x35C+j]),int(r[0x338+j]),(int(r[0x344+j])>>6)&1,int(r[0x3D4+j]),int(r[0x3C8+j]),int(r[0x3B0+j]),int(r[0x3BC+j]))
                o=g.lv_slot[j]
                if isinstance(o,S.Enemy):
                    if o.e_hide: sim[j]=(o.e_wx,o.e_y)
                    else: sim[j]=(o.e_wx,o.e_y,o.e_xs,o.e_ys,o.e_xv,o.e_yv,o.e_pic,o.e_face,o.e_hp,o.e_dmg,o.e_w,o.e_h)
            if nes!=sim:
                bad+=1
                if bad<=verbose:
                    for j in sorted(set(nes)|set(sim)):
                        if nes.get(j)!=sim.get(j): print(f,'slot',j,'nes',nes.get(j),'port',sim.get(j), 'state', getattr(g.lv_slot[j],'e_state',None), 'kind', getattr(g.lv_slot[j],'e_kind',None))
            f+=1
    print('frames',n,'different',bad,'dropped by the NES',lags)
if __name__=='__main__': run(sys.argv[1:] or ['lv1_route0','lv1_route1','lv1_route2'])
