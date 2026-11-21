import numpy as np, json, math, sys
from PIL import Image, ImageDraw
exec(open('preview_render.py').read().split('SX,SY,SZ=g.shape')[0])  # g, pal, C, col
cols=[col(n) for n in pal]
SX,SY,SZ=g.shape
solid=g!=0
def render(az,fn,s=6,el=0.55):
    ca,sa=math.cos(az),math.sin(az)
    def proj(x,y,z):
        cx,cz=x-SX/2,z-SZ/2
        u=cx*ca-cz*sa; w=cx*sa+cz*ca
        return (u*s, -(y*s*0.9) - w*s*el*0.6), w
    xs,ys,zs=np.nonzero(solid)
    faces=[]
    P=np.pad(solid,1)
    for x,y,z in zip(xs,ys,zs):
        i=g[x,y,z]
        if cols[i] is None: continue
        w0=((x-SX/2)*sa+(z-SZ/2)*ca)
        if not P[x+1,y+2,z+1]: faces.append((w0,y,0,x,y,z,i))   # top
        for k,(nx,nz) in enumerate(((1,0),(-1,0),(0,1),(0,-1))):
            if (nx*sa+nz*ca)<0 and not P[x+1+nx,y+1,z+1+nz]:
                faces.append((w0,y,k+1,x,y,z,i))
    faces.sort(key=lambda f:(-f[0],f[1]))
    # bounds
    allp=[proj(x,y,z)[0] for x in (0,SX) for y in (0,SY) for z in (0,SZ)]
    minx=min(p[0] for p in allp);maxx=max(p[0] for p in allp);miny=min(p[1] for p in allp);maxy=max(p[1] for p in allp)
    W=int(maxx-minx)+20;H=int(maxy-miny)+20
    im=Image.new('RGB',(W,H),(205,215,230));d=ImageDraw.Draw(im)
    def P2(x,y,z):
        p=proj(x,y,z)[0]; return (p[0]-minx+10,p[1]-miny+10)
    for w0,_,k,x,y,z,i in faces:
        c=cols[i]
        if k==0: q=[(x,y+1,z),(x+1,y+1,z),(x+1,y+1,z+1),(x,y+1,z+1)]; f=1.0
        elif k==1: q=[(x+1,y,z),(x+1,y+1,z),(x+1,y+1,z+1),(x+1,y,z+1)]; f=0.8
        elif k==2: q=[(x,y,z),(x,y+1,z),(x,y+1,z+1),(x,y,z+1)]; f=0.65
        elif k==3: q=[(x,y,z+1),(x,y+1,z+1),(x+1,y+1,z+1),(x+1,y,z+1)]; f=0.72
        else: q=[(x,y,z),(x,y+1,z),(x+1,y+1,z),(x+1,y,z)]; f=0.58
        d.polygon([P2(*a) for a in q],fill=tuple(int(v*f) for v in c))
    im.save(fn)
for name,deg in (('a',35),('b',215),('c',125)):
    render(math.radians(deg),f'iso_{name}.png')
