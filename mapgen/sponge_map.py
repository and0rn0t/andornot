#!/usr/bin/env python3
"""멩거 스펀지형 큐브 맵 생성기(cube_map.py 의 변형): 3x3x3 에서 각 면의 가운데 + 중심을 뺀 20조각 -> Sponge .schem(v2) -> Sponge .schem(v2) + 미리보기 + 도달 검증.
사용: python3 cube_map.py <출력 폴더>
조각 규칙(멩거 스펀지 1단계): 아래층 8 = 가운데만 빠진 고리 / 가운데층 4 = 모서리 기둥만 / 위층 8 = 아래층과 같은 고리. 총 20조각.
  같은 층 이웃은 평평한 다리로, 층이 다른 이웃은 계단길로 잇는다.
조정 상수: CELL(조각 한 변), GAP(조각 사이 간격), H(층 높이), T(판 두께)
"""
import sys, gzip, struct, math, os
import numpy as np

CELL = 25; GAP = 7; PITCH = CELL + GAP
H = 15            # 층 사이 높이(검은 길이 H칸 걸려 올라간다)
T = 5             # 판 두께
BASE = 14         # 가장 아래 판의 윗면 y(아래 장식 공간)
M = 4  # 큐브 바깥 계단용 여백
SX = CELL * 3 + GAP * 2 + 2 * M
SY = BASE + 2 * H + 12
SZ = SX

air = 'minecraft:air'
palette = {air: 0}
pal_list = [air]
grid = np.zeros((SX, SY, SZ), dtype=np.uint16)

def bid(name):
    if name not in palette:
        palette[name] = len(pal_list); pal_list.append(name)
    return palette[name]

def put(x, y, z, name):
    if 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ:
        grid[x, y, z] = bid(name)

def fill(x0, x1, y0, y1, z0, z1, name):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                put(x, y, z, name)

BLACK = 'minecraft:white_concrete'
PB = 'minecraft:smooth_quartz'
STAIR = 'minecraft:smooth_quartz_stairs'
def stair(facing): return f'{STAIR}[facing={facing},half=bottom,shape=straight]'
DIRS = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}

COLORS = ['red', 'orange', 'yellow', 'lime', 'green', 'cyan', 'light_blue', 'blue', 'purple', 'magenta', 'pink', 'brown', 'gray', 'light_gray', 'red', 'orange', 'yellow', 'lime', 'cyan', 'blue']

# 조각 목록 (cx, cz, cy): 멩거 스펀지 1단계
pieces = []
for cy in (0, 2):
    for cx in range(3):
        for cz in range(3):
            if (cx, cz) != (1, 1):
                pieces.append((cx, cz, cy))
for cx, cz in ((0, 0), (2, 0), (0, 2), (2, 2)):
    pieces.append((cx, cz, 1))
pieces.sort(key=lambda p: (p[2], p[1], p[0]))
color_of = {p: COLORS[i] for i, p in enumerate(pieces)}
tmpl_of = {p: i % 4 for i, p in enumerate(pieces)}
rot_of = {p: i % 4 for i, p in enumerate(pieces)}

def origin(p):  # 조각 왼쪽 위 x,z, 윗면 y
    return p[0] * PITCH + M, p[2] * H + BASE, p[1] * PITCH + M

def ytop(cy): return BASE + cy * H

# ---------- 판 본체 ----------
def sticker(color, lx, lz):
    """윗면 스티커 무늬: 3x3 칸(7x7) + 검은 격자선. 반환: 블록 이름"""
    main = f'minecraft:{color}_concrete'; acc = f'minecraft:{color}_terracotta'
    if lx in (0, CELL - 1) or lz in (0, CELL - 1):
        return BLACK
    if lx in (8, 16) or lz in (8, 16):
        return PB
    ti = (lx - 1) // 8; tj = (lz - 1) // 8
    return main if (ti + tj) % 2 == 0 else acc

def build_slab(p):
    x0, ys, z0 = origin(p)
    col = color_of[p]
    for lx in range(CELL):
        for lz in range(CELL):
            top = sticker(col, lx, lz)
            put(x0 + lx, ys, z0 + lz, top)
            acc = f'minecraft:{col}_terracotta'
            main = f'minecraft:{col}_concrete'
            for d in range(1, T):
                edge = lx in (0, CELL - 1) or lz in (0, CELL - 1)
                if edge:
                    # 옆면: 위 검은 테두리, 가운데 조각 색(콘크리트/테라코타 번갈아), 맨 아래 검은 테두리
                    if d == 1 or d == T - 1: blk = BLACK
                    else: blk = main if d == 2 else acc
                else:
                    blk = acc
                put(x0 + lx, ys - d, z0 + lz, blk)
    # 아래 장식: 거꾸로 선 피라미드(2칸씩 줄어듦) + 가운데 기둥
    for k in range(1, 4):
        ins = k * 2 + 1
        if CELL - 2 * ins < 3: break
        fill(x0 + ins, x0 + CELL - 1 - ins, ys - T - k + 1, ys - T - k + 1, z0 + ins, z0 + CELL - 1 - ins, PB if k % 2 else BLACK)
    # 모서리 등(기둥 1x1 + 바다등): 길(깊이 0..2)과 겹치지 않게 안쪽 3칸에
    for cx_, cz_ in ((3, 3), (CELL - 4, 3), (3, CELL - 4), (CELL - 4, CELL - 4)):
        put(x0 + cx_, ys + 1, z0 + cz_, PB)
        put(x0 + cx_, ys + 2, z0 + cz_, 'minecraft:sea_lantern')

def col_block(p, x, z):  # 지형 블록(바닥 무늬와 같은 색)
    return sticker(color_of[p], x, z)

def raise_box(p, xa, xb, za, zb, h):
    x0, ys, z0 = origin(p)
    for lx in range(xa, xb + 1):
        for lz in range(za, zb + 1):
            for d in range(1, h + 1):
                put(x0 + lx, ys + d, z0 + lz, col_block(p, lx, lz))

def staircase(x, ys, z, dirname, n, width_axis_cells, fill_below=BLACK):
    """(x,z) 에서 dirname 방향으로 n칸 올라가는 계단. width_axis_cells = 폭 방향 오프셋 목록.
    바닥 윗면 높이 ys(그 블록 y). 계단 k 번째 칸: ys+1+k 에 계단, 아래 ys+1..ys+k 는 검은 블록."""
    dx, dz = DIRS[dirname]
    px, pz = (-dz, dx)  # 폭 방향
    for k in range(n):
        for w in width_axis_cells:
            cx = x + dx * k + px * w; cz = z + dz * k + pz * w
            for y in range(ys + 1, ys + 1 + k):
                put(cx, y, cz, fill_below)
            put(cx, ys + 1 + k, cz, stair(dirname))

def side_stairs(p, box, h, level_y_off=0):
    """box(xa,xb,za,zb) 둘레 4면에 폭 3(가운데) 계단 한 칸. 박스 바깥 한 칸에 놓는다(바닥 윗면은 ys+level_y_off)."""
    xa, xb, za, zb = box
    x0, ys, z0 = origin(p)
    cxm = (xa + xb) // 2; czm = (za + zb) // 2
    base = ys + level_y_off
    # 서쪽 바깥: 동쪽(박스 쪽)으로 오른다
    staircase(x0 + xa - 1, base, z0 + czm, 'east', 1, (-1, 0, 1))
    staircase(x0 + xb + 1, base, z0 + czm, 'west', 1, (-1, 0, 1))
    staircase(x0 + cxm, base, z0 + za - 1, 'south', 1, (-1, 0, 1))
    staircase(x0 + cxm, base, z0 + zb + 1, 'north', 1, (-1, 0, 1))

def terrain(p):
    x0, ys, z0 = origin(p)
    t = tmpl_of[p]
    if t == 0:  # 계단식 피라미드(중앙 고지)
        layers = [((5, 19, 5, 19), 1), ((8, 16, 8, 16), 2), ((10, 14, 10, 14), 3)]
        for box, h in layers:
            raise_box(p, box[0], box[1], box[2], box[3], h)
        for i, (box, h) in enumerate(layers):
            side_stairs(p, box, h, i)
    elif t == 1:  # 모서리 4탑(높이 3) + 안쪽 계단
        for (a, b) in ((4, 8), (16, 20)):
            for (c, d) in ((4, 8), (16, 20)):
                raise_box(p, a, b, c, d, 3)
        # 탑 안쪽 계단(3칸): 각 탑에서 중앙 쪽으로
        for (tx, tz, dn, sx, sz) in ((8, 6, 'west', 9, 6), (16, 6, 'east', 15, 6), (8, 18, 'west', 9, 18), (16, 18, 'east', 15, 18)):
            pass
        for (sx, sz, dn) in ((9, 6, 'west'), (15, 6, 'east'), (9, 18, 'west'), (15, 18, 'east')):
            staircase(x0 + sx, ys, z0 + sz, dn, 3, (-1, 0, 1))
        # 가운데 낮은 단(+1) 십자
        raise_box(p, 11, 13, 4, 20, 1)
        raise_box(p, 4, 20, 11, 13, 1)
    elif t == 2:  # 아레나: 문 4개가 있는 두꺼운 벽(높이 2) + 가운데 단
        ring = [(6, 18, 6, 7), (6, 18, 17, 18), (6, 7, 6, 18), (17, 18, 6, 18)]
        for (a, b, c, d) in ring:
            raise_box(p, a, b, c, d, 2)
        # 문 3칸 뚫기
        for lx in (11, 12, 13):
            for lz in (6, 7, 17, 18):
                for d in (1, 2): put(x0 + lx, ys + d, z0 + lz, air)
        for lz in (11, 12, 13):
            for lx in (6, 7, 17, 18):
                for d in (1, 2): put(x0 + lx, ys + d, z0 + lz, air)
        raise_box(p, 10, 14, 10, 14, 1)
    else:  # 대각선 계단식 고지(높이 1~3)
        r = rot_of[p]
        for lx in range(4, 21):
            for lz in range(4, 21):
                u, v = lx, lz
                for _ in range(r % 4):
                    u, v = CELL - 1 - v, u
                s = u + v
                h = 0
                if s >= 24: h = 1
                if s >= 32: h = 2
                if s >= 38: h = 3
                for d in range(1, h + 1):
                    put(x0 + lx, ys + d, z0 + lz, col_block(p, lx, lz))

# ---------- 검은 길 ----------
links = []  # (lower, upper, dir_name)
def nb(p, d):
    dx, dz = DIRS[d]; return (p[0] + dx, p[1] + dz)
pset = set(pieces)
for p in pieces:
    for d in DIRS:
        q0 = nb(p, d)
        for cy2 in ((p[2] + 1,) if p[2] == 0 else ()):
            q = (q0[0], q0[1], cy2)
            if q in pset:
                # 허용 링크: 아래층 변조각 -> 가운데(모서리/중심) ; 가운데 모서리 -> 위층 ; 가운데 중심 -> 위층
                links.append((p, q, d))

def build_flat(a, b, d):
    """같은 층 이웃: 변을 따라 21..23 칸 폭 3 다리(계단길은 3..20 을 쓴다)"""
    x0, y0, z0 = origin(a)
    y = y0
    for k in range(21, 24):
        for g in range(1, GAP + 1):
            if d == 'west': put(x0 - g, y, z0 + k, BLACK); put(x0 - g, y - 1, z0 + k, PB)
            elif d == 'east': put(x0 + CELL - 1 + g, y, z0 + k, BLACK); put(x0 + CELL - 1 + g, y - 1, z0 + k, PB)
            elif d == 'north': put(x0 + k, y, z0 - g, BLACK); put(x0 + k, y - 1, z0 - g, PB)
            else: put(x0 + k, y, z0 + CELL - 1 + g, BLACK); put(x0 + k, y - 1, z0 + CELL - 1 + g, PB)

def build_outer(p, side):
    """가운데층 모서리 기둥 -> 위층: 위층 모서리 판이 바로 위에 있어서 판 안쪽 길은 막히므로, 기둥 바깥 면에 계단을 붙여 올라간다.
    계단(깊이 0..2)은 판 바깥쪽 3칸 띠 위(a=3..17), 착지 3칸(a=18..20) 끝이 위층 판의 바깥 변에 바로 닿는다(간격 0)."""
    x0, yl, z0 = origin(p)
    yu = ytop(2)
    n = H
    for k in range(n + 3):
        for w in range(3):
            if side in ('west', 'east'):
                cx = x0 - 1 - w if side == 'west' else x0 + CELL + w
                cz = z0 + 3 + k
                dn = 'south'
            else:
                cz = z0 - 1 - w if side == 'north' else z0 + CELL + w
                cx = x0 + 3 + k
                dn = 'east'
            if k < n:
                for y in range(yl + 1, yl + 1 + k): put(cx, y, cz, BLACK)
                put(cx, yl + 1 + k, cz, stair(dn))
            else:
                for y in range(yl + 1, yu + 1): put(cx, y, cz, BLACK)

def build_link(lo, up, d, idx):
    x0, yl, z0 = origin(lo)
    yu = ytop(up[2])
    dx, dz = DIRS[d]
    # 공유하는 변 쪽 깊이 0..2, 변을 따라 a=3..20
    # 아래층->가운데층(lo 가 아래층): 거꾸로(착지 3..5). 가운데층->위층: 앞으로(a=6 에서 시작, 착지 21..23). 같은 변에서 두 길이 안 겹치게 한다.
    forward = (lo[2] == 1)
    a0 = 6
    n = H
    if d in ('west', 'east'):
        # 공유 변이 x 방향(서/동), 변을 따라 z 로 간다
        ex = x0 if d == 'west' else x0 + CELL - 1
        inward_x = 1 if d == 'west' else -1  # 판 안쪽으로 들어오는 방향(깊이 증가)
        # 계단은 z 방향으로 올라간다. 폭 3 = 깊이 0..2
        if forward:
            zs, dn = z0 + a0, 'south'
        else:
            zs, dn = z0 + 20, 'north'
        for k in range(n):
            cz = zs + (k if forward else -k)
            for w in range(3):
                cx = ex + inward_x * w
                for y in range(yl + 1, yl + 1 + k): put(cx, y, cz, BLACK)
                put(cx, yl + 1 + k, cz, stair(dn))
        # 착지(3칸) + 기둥
        for k in range(n, n + 3):
            cz = zs + (k if forward else -k)
            for w in range(3):
                cx = ex + inward_x * w
                for y in range(yl + 1, yu + 1): put(cx, y, cz, BLACK)
        # 다리(간격 5칸, 폭 3): 착지 3칸 중 가운데 한 줄만 건너가는 게 아니라 폭 3 모두
        for k in range(n, n + 3):
            cz = zs + (k if forward else -k)
            for g in range(1, GAP + 1):
                cx = ex + (-g if d == 'west' else g)
                put(cx, yu, cz, BLACK)
                put(cx, yu - 1, cz, PB)
    else:
        ez = z0 if d == 'north' else z0 + CELL - 1
        inward_z = 1 if d == 'north' else -1
        if forward:
            xs, dn = x0 + a0, 'east'
        else:
            xs, dn = x0 + 20, 'west'
        for k in range(n):
            cx = xs + (k if forward else -k)
            for w in range(3):
                cz = ez + inward_z * w
                for y in range(yl + 1, yl + 1 + k): put(cx, y, cz, BLACK)
                put(cx, yl + 1 + k, cz, stair(dn))
        for k in range(n, n + 3):
            cx = xs + (k if forward else -k)
            for w in range(3):
                cz = ez + inward_z * w
                for y in range(yl + 1, yu + 1): put(cx, y, cz, BLACK)
        for k in range(n, n + 3):
            cx = xs + (k if forward else -k)
            for g in range(1, GAP + 1):
                cz = ez + (-g if d == 'north' else g)
                put(cx, yu, cz, BLACK)
                put(cx, yu - 1, cz, PB)

def main(out):
    os.makedirs(out, exist_ok=True)
    for p in pieces: build_slab(p)
    for p in pieces: terrain(p)
    # 채택할 링크: 아래층 변조각 -> 가운데 층 전부, 가운데 층 -> 위층 전부
    sel = [(a, b, d) for (a, b, d) in links]
    for i, (a, b, d) in enumerate(sel):
        build_link(a, b, d, i)
    for p in pieces:
        if p[2] == 1:
            for side in ('west' if p[0] == 0 else 'east', 'north' if p[1] == 0 else 'south'):
                build_outer(p, side)
    nflat = 0
    for p in pieces:
        for d in ('east', 'south'):
            q0 = nb(p, d); q = (q0[0], q0[1], p[2])
            if q in pset:
                build_flat(p, q, d); nflat += 1
    print('flat bridges', nflat)
    write_schem(os.path.join(out, 'sponge_map.schem'))
    return sel

# ---------- 파일 출력(Sponge schematic v2) ----------
def varint(v):
    b = bytearray()
    while True:
        t = v & 0x7F; v >>= 7
        if v: b.append(t | 0x80)
        else: b.append(t); break
    return bytes(b)

def nbt_str(s):
    e = s.encode('utf-8'); return struct.pack('>H', len(e)) + e
def tag(tid, name, payload): return bytes([tid]) + nbt_str(name) + payload

def write_schem(path):
    data = bytearray()
    for y in range(SY):
        for z in range(SZ):
            for x in range(SX):
                data += varint(int(grid[x, y, z]))
    pal = b''.join(tag(3, n, struct.pack('>i', i)) for n, i in palette.items()) + b'\x00'
    root = (tag(3, 'Version', struct.pack('>i', 2)) + tag(3, 'DataVersion', struct.pack('>i', 3700))
            + tag(2, 'Width', struct.pack('>h', SX)) + tag(2, 'Height', struct.pack('>h', SY)) + tag(2, 'Length', struct.pack('>h', SZ))
            + tag(3, 'PaletteMax', struct.pack('>i', len(palette)))
            + tag(10, 'Palette', pal)
            + tag(7, 'BlockData', struct.pack('>i', len(data)) + bytes(data))
            + tag(11, 'Offset', struct.pack('>i', 3) + struct.pack('>iii', 0, 0, 0))
            + b'\x00')
    nbt = tag(10, 'Schematic', root)
    with gzip.open(path, 'wb') as f: f.write(nbt)

# ---------- 도달 검증 ----------
def solid(x, y, z):
    if not (0 <= x < SX and 0 <= y < SY and 0 <= z < SZ): return False
    return grid[x, y, z] != 0

def verify():
    from collections import deque
    def standable(x, y, z):
        return solid(x, y - 1, z) and not solid(x, y, z) and not solid(x, y + 1, z)
    sx, sy, sz = origin(pieces[0])
    start = (sx + 12, sy + 1, sz + 12)
    # 시작: 첫 조각 중앙은 지형일 수 있으니 서 있을 수 있는 가장 가까운 점 탐색
    seen = {start: 0}
    if not standable(*start):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                for dy in range(0, 5):
                    s = (sx + 12 + dx, sy + 1 + dy, sz + 12 + dz)
                    if standable(*s): start = s; break
                else: continue
                break
    seen = {start}
    dq = deque([start])
    while dq:
        x, y, z = dq.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            for ny in (y + 1, y, y - 1, y - 2, y - 3):
                if ny == y + 1 and (solid(x, y + 1, z) or solid(x, y + 2, z)):  # 점프 공간
                    continue
                if standable(nx, ny, nz) and (nx, ny, nz) not in seen:
                    # 오를 때(+1)는 점프, 내릴 때는 자유
                    seen.add((nx, ny, nz)); dq.append((nx, ny, nz))
                    break
    reached = {}
    for p in pieces:
        x0, ys, z0 = origin(p)
        cnt = sum(1 for (x, y, z) in seen if x0 <= x < x0 + CELL and z0 <= z < z0 + CELL and ys - 1 <= y <= ys + 5)
        reached[p] = cnt
    return reached, len(seen)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    sel = main(out)
    r, total = verify()
    print('standable cells reached:', total)
    for p in pieces: print(p, color_of[p], 'tmpl', tmpl_of[p], 'reached', r[p])
    print('palette', len(palette), 'size', SX, SY, SZ, 'links', len(sel))
    np.save(os.path.join(out, 'grid.npy'), grid)
    import json
    json.dump(pal_list, open(os.path.join(out, 'pal.json'), 'w'))
