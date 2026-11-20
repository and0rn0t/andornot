# 미니맵 리소스 팩 생성기. 실행: python gen_pack.py  -> pack/ 폴더와 andornot-pack.zip 을 만들고 SHA-1 을 출력한다.
# 베이크한 지도 이미지(map1~4.png)가 pack/assets/andornot/textures/font/ 에 이미 있으면 덮어쓰지 않는다.
import json, os, zipfile, hashlib, struct, zlib

ROOT = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(ROOT, "pack")
FONT_TEX = os.path.join(PACK, "assets", "andornot", "textures", "font")
MAP_PX = 100         # 지도 이미지 한 변(픽셀) = 화면에서 차지하는 크기(GUI 픽셀)
MAP_TOP = 5          # 보스바 글자줄 윗변에서 지도 윗변까지 거리(GUI 픽셀). 보스바 1번째 줄 기준
TEX_PX = 100        # 지도 이미지 해상도(픽셀). 화면 표시 크기(MAP_PX)와 별개
SLOTS = 4            # 지도 슬롯 개수(월드 4개까지)

def png(path, w, h, rgba):
    raw = b"".join(b"\x00" + b"".join(bytes(rgba(x, y)) for x in range(w)) for y in range(h))
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

W = (255, 255, 255, 255); T = (0, 0, 0, 0)
# 점(팀원) 3x3, 내 표시(흰 마름모) 5x5
png(os.path.join(FONT_TEX, "dot.png"), 3, 3, lambda x, y: W)
diamond = ["..X..", ".XXX.", "XXXXX", ".XXX.", "..X.."]
png(os.path.join(FONT_TEX, "me.png"), 5, 5, lambda x, y: W if diamond[y][x] == "X" else T)
# 지도 자리표시(베이크 전): 어두운 바탕 + 8칸 격자
for s in range(1, SLOTS + 1):
    p = os.path.join(FONT_TEX, "map%d.png" % s)
    if not os.path.exists(p):
        def px(x, y):
            g = (x % 32 == 0) or (y % 32 == 0)
            return (70, 70, 70, 255) if g else (40, 40, 40, 255)
        png(p, TEX_PX, TEX_PX, px)
# 보스바 기본 막대 그림을 투명으로 덮어서 흰색 보스바는 글자만 보이게 한다(1.20.2+ 스프라이트 경로)
BB = os.path.join(PACK, "assets", "minecraft", "textures", "gui", "sprites", "boss_bar")
png(os.path.join(BB, "white_background.png"), 182, 5, lambda x, y: T)
png(os.path.join(BB, "white_progress.png"), 182, 5, lambda x, y: T)

# 폰트: 공백 글자(가로 이동), 지도 글자, 행마다 높이가 다른 점/내 표시 글자
providers = []
adv = {}
for k in range(11):
    adv[chr(0xE000 + k)] = 2 ** k
    adv[chr(0xE010 + k)] = -(2 ** k)
providers.append({"type": "space", "advances": adv})
for s in range(SLOTS):
    providers.append({"type": "bitmap", "file": "andornot:font/map%d.png" % (s + 1),
                      "ascent": 7 - MAP_TOP, "height": MAP_PX, "chars": [chr(0xE100 + s)]})
for y in range(MAP_PX):
    providers.append({"type": "bitmap", "file": "andornot:font/dot.png",
                      "ascent": 7 - (MAP_TOP + y - 1), "height": 3, "chars": [chr(0xE200 + y)]})
    providers.append({"type": "bitmap", "file": "andornot:font/me.png",
                      "ascent": 7 - (MAP_TOP + y - 2), "height": 5, "chars": [chr(0xE300 + y)]})
fd = os.path.join(PACK, "assets", "andornot", "font")
os.makedirs(fd, exist_ok=True)
with open(os.path.join(fd, "mm.json"), "w", encoding="utf-8") as f:
    json.dump({"providers": providers}, f, indent=1)  # ensure_ascii 기본값 ->  형태로 저장

# 1.21.9 이후 형식(min_format/max_format)과 예전 형식(pack_format/supported_formats)을 같이 적어 어느 클라이언트에서도 호환으로 보이게 한다
meta = {"pack": {"description": "andornot minimap", "pack_format": 34,
                 "supported_formats": {"min_inclusive": 34, "max_inclusive": 999},
                 "min_format": 34, "max_format": 999}}
with open(os.path.join(PACK, "pack.mcmeta"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)

# 같은 입력이면 같은 해시가 나오도록 파일 순서와 시간을 고정해서 압축한다
zp = os.path.join(ROOT, "andornot-pack.zip")
files = []
for d, _, fs in os.walk(PACK):
    for n in fs:
        full = os.path.join(d, n)
        files.append((os.path.relpath(full, PACK).replace(os.sep, "/"), full))
files.sort()
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for rel, full in files:
        zi = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        with open(full, "rb") as f:
            z.writestr(zi, f.read())
print("zip:", zp)
print("sha1:", hashlib.sha1(open(zp, "rb").read()).hexdigest())
