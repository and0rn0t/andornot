#!/usr/bin/env python3
"""큐브 맵 생성기 v2: 3x3x3 큐브 퍼즐 형태의 플랫폼 맵 -> Sponge .schem(v2) + 미리보기 + 도달 검증.
사용: python3 cube_map.py <출력 폴더>
조각 규칙: 아래층 4(상하좌우) / 가운데층 5(모서리 4 + 중앙) / 위층 4(상하좌우) = 13조각.
  색: 세로줄(cx,cz)마다 색이 하나. 같은 세로줄(아래층-위층 변 조각)은 같은 색, 가운데 조각은 검정.
  길: 위층 4조각 <-> 가운데 조각(계단길 + 다리) / 가운데층 모서리 4조각끼리 사각형 순환 다리 / 아래층 4조각은 가운데와 이어진 장식 지지대뿐(걸을 수 없음).
  조명: 밝기 블록(minecraft:light, 밝기 15)을 곳곳에 숨겨 둔다(밤 전투용).
조정 상수: CELL(조각 한 변), GAP(조각 사이 간격), H(층 높이), T(판 두께)
"""
import sys, gzip, struct, math, os
import numpy as np

CELL = 25; GAP = 5; PITCH = CELL + GAP
H = 18            # 층 사이 높이(검은 길이 H칸 걸려 올라간다. 계단 H + 착지 3 이 변(25)에 들어가야 한다)
T = 5             # 판 두께
BASE = 14         # 가장 아래 판의 윗면 y(아래 장식 공간)
SX = CELL * 3 + GAP * 2
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

BLACK = 'minecraft:black_concrete'
PB = 'minecraft:polished_blackstone'
STAIR = 'minecraft:polished_blackstone_brick_stairs'
def stair(facing): return f'{STAIR}[facing={facing},half=bottom,shape=straight]'
DIRS = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}


# 조각 목록 (cx, cz, cy)
pieces = []
for cy in (0, 2):
    for cx, cz in ((1, 0), (0, 1), (2, 1), (1, 2)):
        pieces.append((cx, cz, cy))
for cx, cz in ((0, 0), (2, 0), (0, 2), (2, 2), (1, 1)):
    pieces.append((cx, cz, 1))
pieces.sort(key=lambda p: (p[2], p[1], p[0]))
COL_BY_COLUMN = {(1, 0): 'red', (0, 1): 'orange', (2, 1): 'yellow', (1, 2): 'lime',
                 (0, 0): 'cyan', (2, 0): 'light_blue', (0, 2): 'purple', (2, 2): 'magenta', (1, 1): 'black'}
color_of = {p: COL_BY_COLUMN[(p[0], p[1])] for p in pieces}
tmpl_of = {p: i % 4 for i, p in enumerate(pieces)}
rot_of = {p: i % 4 for i, p in enumerate(pieces)}

def origin(p):  # 조각 왼쪽 위 x,z, 윗면 y
    return p[0] * PITCH, p[2] * H + BASE, p[1] * PITCH

def ytop(cy): return BASE + cy * H

# ---------- 판 본체 ----------
def sticker(color, lx, lz):
    """윗면 스티커 무늬: 3x3 칸(7x7) + 검은 격자선. 반환: 블록 이름"""
    main = f'minecraft:{color}_concrete'; acc = f'minecraft:{color}_terracotta'
    if lx in (0, CELL - 1) or lz in (0, CELL - 1):
        return BLACK
    if lx in (8, 16) or lz in (8, 16):
        return 'minecraft:gray_concrete' if color == 'black' else PB
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
    for k in range(1, 8):
        ins = k * 2 + 1
        if CELL - 2 * ins < 3: break
        fill(x0 + ins, x0 + CELL - 1 - ins, ys - T - k + 1, ys - T - k + 1, z0 + ins, z0 + CELL - 1 - ins, PB if k % 2 else BLACK)
    # 모서리 장식 기둥(1x1, 높이 2)
    for cx_, cz_ in ((3, 3), (CELL - 4, 3), (3, CELL - 4), (CELL - 4, CELL - 4)):
        put(x0 + cx_, ys + 1, z0 + cz_, PB)
        put(x0 + cx_, ys + 2, z0 + cz_, BLACK)

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
        for cy2 in ((p[2] + 1,) if p[:2] == (1, 1) else ()):
            q = (q0[0], q0[1], cy2)
            if q in pset:
                # 허용 링크: 아래층 변조각 -> 가운데(모서리/중심) ; 가운데 모서리 -> 위층 ; 가운데 중심 -> 위층
                links.append((p, q, d))

def build_link(lo, up, d, idx):
    x0, yl, z0 = origin(lo)
    yu = ytop(up[2])
    dx, dz = DIRS[d]
    # 공유하는 변 쪽 깊이 0..2, 변을 따라 a=3..20
    forward = (idx % 2 == 0)
    n = H
    if d in ('west', 'east'):
        # 공유 변이 x 방향(서/동), 변을 따라 z 로 간다
        ex = x0 if d == 'west' else x0 + CELL - 1
        inward_x = 1 if d == 'west' else -1  # 판 안쪽으로 들어오는 방향(깊이 증가)
        # 계단은 z 방향으로 올라간다. 폭 3 = 깊이 0..2
        if forward:
            zs, dn = z0 + 2, 'south'
        else:
            zs, dn = z0 + 22, 'north'
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
            xs, dn = x0 + 2, 'east'
        else:
            xs, dn = x0 + 22, 'west'
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

LIGHT = 'minecraft:light[level=15,waterlogged=false]'
lights = []

def add_light_scan():
    """계단 4칸마다(계단 위 2칸 높이), 다리 5칸마다, 판 위 6칸 격자로 밝기 블록을 숨긴다(빈 칸일 때만)."""
    # 판 위: 지형 위 첫 빈 칸(바닥 +1 ~ +5)
    for p in pieces:
        x0, ys, z0 = origin(p)
        for lx in (2, 8, 14, 20, 24 - 2):
            for lz in (2, 8, 14, 20, 24 - 2):
                for y in range(ys + 1, ys + 6):
                    if grid[x0 + lx, y, z0 + lz] == 0:
                        lights.append((x0 + lx, y, z0 + lz)); break
    # 계단/다리: 바닥(계단 블록) 위 2칸에
    stair_ids = {i for n, i in palette.items() if 'stairs' in n}
    xs, ys_, zs = np.nonzero(np.isin(grid, list(stair_ids)))
    for x, y, z in zip(xs, ys_, zs):
        if (x + y + z) % 4 == 0 and grid[x, y + 1, z] == 0 and grid[x, y + 2, z] == 0:
            lights.append((x, y + 2, z))
    for (x, y, z) in lights:
        if grid[x, y, z] == 0: put(x, y, z, LIGHT)
    add_light_fill()

def add_light_fill(target=9, limit=600):
    """걸을 수 있는 칸 중 밝기(밝기 블록까지 맨해튼 거리로 근사: 15 - 거리)가 target 미만인 곳에 밝기 블록을 더 둔다.
    실제 빛 퍼짐은 블록에 막히므로 이 값은 낙관적인 근사다(미검증: 서버에서 F3 으로 밝기 확인)."""
    lid = palette[LIGHT]
    src = np.argwhere(grid == lid)
    sol = (grid != 0) & (grid != lid)
    st = sol[:, :-3, :] & ~sol[:, 1:-2, :] & ~sol[:, 2:-1, :]
    pts = np.argwhere(st); pts[:, 1] += 1
    best = np.zeros(len(pts), dtype=int)
    for s_ in src:
        best = np.maximum(best, 15 - np.abs(pts - s_).sum(axis=1))
    added = 0
    while added < limit:
        i = int(np.argmin(best))
        if best[i] >= target: break
        x, y, z = pts[i]
        put(int(x), int(y) + 1, int(z), LIGHT)
        best = np.maximum(best, 15 - np.abs(pts - np.array([x, y + 1, z])).sum(axis=1))
        added += 1
    print('light fill added', added, 'min', int(best.min()), 'mean', round(float(best.mean()), 1))

def build_loop():
    """가운데층 모서리 4조각을 잇는 사각형 순환 다리(폭 3, 가운데 a=11..13). 모서리 -> 빠진 변 조각 자리를 가로지른다."""
    yv = ytop(1)
    def span(a, b, axis):
        xa, _, za = origin(a); xb, _, zb = origin(b)
        if axis == 'x':   # a -> b 가 +x 방향 (같은 z 줄)
            for xx in range(xa + CELL, xb):
                for w in (11, 12, 13):
                    put(xx, yv, za + w, BLACK); put(xx, yv - 1, za + w, PB)
                    if (xx - xa) % 6 == 0: lights.append((xx, yv + 1, za + 12))
        else:
            for zz in range(za + CELL, zb):
                for w in (11, 12, 13):
                    put(xa + w, yv, zz, BLACK); put(xa + w, yv - 1, zz, PB)
                    if (zz - za) % 6 == 0: lights.append((xa + 12, yv + 1, zz))
    span((0, 0, 1), (2, 0, 1), 'x')
    span((0, 2, 1), (2, 2, 1), 'x')
    span((0, 0, 1), (0, 2, 1), 'z')
    span((2, 0, 1), (2, 2, 1), 'z')

def build_braces():
    """아래층 4조각과 가운데 조각을 잇는 장식 지지대(3폭, 간격 5칸). 윗면이 가운데 조각 바닥 높이라서 걸어서 못 쓴다."""
    ytop_mid = ytop(1)
    ytop_lo = ytop(0)
    for lo, d in (((1, 0, 0), 'south'), ((0, 1, 0), 'east'), ((2, 1, 0), 'west'), ((1, 2, 0), 'north')):
        x0, _, z0 = origin(lo)
        y0 = ytop_lo - 4
        y1 = ytop_mid - T + 1
        for g in range(GAP):
            for w in (11, 12, 13):
                if d == 'south': cx, cz = x0 + w, z0 + CELL + g
                elif d == 'north': cx, cz = x0 + w, z0 - 1 - g
                elif d == 'east': cx, cz = x0 + CELL + g, z0 + w
                else: cx, cz = x0 - 1 - g, z0 + w
                for y in range(y0, y1 + 1):
                    put(cx, y, cz, PB if (y - y0) % 6 == 5 else BLACK)

def main(out):
    os.makedirs(out, exist_ok=True)
    for p in pieces: build_slab(p)
    for p in pieces: terrain(p)
    # 채택할 링크: 아래층 변조각 -> 가운데 층 전부, 가운데 층 -> 위층 전부
    sel = [(a, b, d) for (a, b, d) in links]
    for i, (a, b, d) in enumerate(sel):
        build_link(a, b, d, i)
    build_loop()
    build_braces()
    add_light_scan()
    write_schem(os.path.join(out, 'cube_map.schem'))
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
    v = grid[x, y, z]
    return v != 0 and v != palette.get(LIGHT, -1)

def reach_from(p0):
    """p0 조각 윗면에서 걸어서(1칸 오름 허용) 닿는 조각 집합."""
    from collections import deque
    def standable(x, y, z):
        return solid(x, y - 1, z) and not solid(x, y, z) and not solid(x, y + 1, z)
    sx, sy, sz = origin(p0)
    start = None
    for (lx, lz) in ((12, 1), (1, 12), (12, 23), (23, 12), (1, 1)):
        c = (sx + lx, sy + 1, sz + lz)
        if standable(*c): start = c; break
    seen = {start}
    dq = deque([start])
    while dq:
        x, y, z = dq.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            for ny in (y + 1, y, y - 1, y - 2, y - 3):
                if ny == y + 1 and (solid(x, y + 1, z) or solid(x, y + 2, z)):
                    continue
                if standable(nx, ny, nz) and (nx, ny, nz) not in seen:
                    seen.add((nx, ny, nz)); dq.append((nx, ny, nz)); break
    out = set()
    for p in pieces:
        x0, ys, z0 = origin(p)
        if any(x0 <= x < x0 + CELL and z0 <= z < z0 + CELL and ys - 1 <= y <= ys + 6 for (x, y, z) in seen):
            out.add(p)
    return out, len(seen)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    sel = main(out)
    print('size', SX, SY, SZ, 'palette', len(palette), 'lights', len(lights), 'links', len(sel))
    # 구역 검증: 기대 = {가운데+위층 4}, {가운데층 모서리 4}, {아래층 각 1개(단독)}
    seen_groups = []
    for p in pieces:
        r, n = reach_from(p)
        grp = tuple(sorted(r))
        if grp not in seen_groups:
            seen_groups.append(grp)
    for g in seen_groups:
        print('group:', [(q, color_of[q]) for q in g])
    np.save(os.path.join(out, 'grid.npy'), grid)
    import json
    json.dump(pal_list, open(os.path.join(out, 'pal.json'), 'w'))
