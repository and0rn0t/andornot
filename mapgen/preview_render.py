import numpy as np, json, sys
from PIL import Image, ImageDraw
g=np.load('grid.npy'); pal=json.load(open('pal.json'))
C={'red':(200,40,40),'orange':(240,130,30),'yellow':(235,200,40),'lime':(120,200,30),'green':(70,130,40),'cyan':(30,140,150),'light_blue':(60,160,220),'blue':(50,60,170),'purple':(130,50,180),'magenta':(190,60,190),'pink':(240,140,180),'white':(225,225,225),'brown':(110,70,40)}
def col(n):
    n=n.split('[')[0].replace('minecraft:','')
    if n=='air' or n.startswith('light'): return None
    for k,v in C.items():
        if n.startswith(k+'_concrete'): return v
        if n.startswith(k+'_terracotta'): return tuple(int(c*0.72) for c in v)
    if n=='black_concrete': return (20,20,24)
    if n=='polished_blackstone': return (48,44,52)
    if 'blackstone' in n: return (60,56,66)
    if n=='sea_lantern': return (190,230,230)
    return (128,128,128)
cols=[col(n) for n in pal]
SX,SY,SZ=g.shape
def render(az,fn,scale=5):
    import math
    ca,sa=math.cos(az),math.sin(az)
    W=int((SX+SZ)*scale*0.9)+40; Hh=int(SY*scale*1.0+(SX+SZ)*scale*0.5)+40
    im=Image.new('RGB',(W,Hh),(205,215,230)); d=ImageDraw.Draw(im)
    pts=[]
    # painter: sort by depth
    xs,ys,zs=np.nonzero(g)
    ids=g[xs,ys,zs]
    items=[]
    for x,y,z,i in zip(xs,ys,zs,ids):
        # 노출면만
        top = y+1>=SY or g[x,y+1,z]==0
        def e(a,b,c): return not(0<=a<SX and 0<=b<SY and 0<=c<SZ) or g[a,b,c]==0
        sx_ = e(x+1,y,z); sz_ = e(x,y,z+1); sxm=e(x-1,y,z); szm=e(x,y,z-1)
        if not(top or sx_ or sz_ or sxm or szm): continue
        # 회전 좌표
        cx,cz=x-SX/2,z-SZ/2
        rx=cx*ca-cz*sa; rz=cx*sa+cz*ca
        items.append((rz*1.0+0.0*rx, rx, y, x,y,z,i,top,(sx_,sz_,sxm,szm)))
    items.sort(key=lambda t:(-t[0],t[2]))
    for dep,rx,_,x,y,z,i,top,sides in items:
        c=cols[i]
        if c is None: continue
        px=W/2+rx*scale; py=Hh-30-(y*scale)+dep*scale*0.5
        s=scale
        # 윗면 마름모
        if top:
            d.polygon([(px,py-s),(px+s,py-s*0.5),(px,py),(px-s,py-s*0.5)],fill=c)
        # 앞면 2개(관찰자 쪽)
        dk=tuple(int(v*0.78) for v in c); dk2=tuple(int(v*0.6) for v in c)
        d.polygon([(px-s,py-s*0.5),(px,py),(px,py+s),(px-s,py+s*0.5)],fill=dk)
        d.polygon([(px,py),(px+s,py-s*0.5),(px+s,py+s*0.5),(px,py+s)],fill=dk2)
    im.save(fn)
import math
render(math.radians(35),'iso_a.png',5)
render(math.radians(35+180),'iso_b.png',5)
