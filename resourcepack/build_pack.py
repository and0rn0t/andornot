# mck_pack 리소스 팩 빌드: python3 resourcepack/build_pack.py -> resourcepack/mck_pack.zip 생성 + SHA-1 출력.
# 같은 입력이면 같은 해시가 나오게 파일 순서와 시간을 고정해서 압축한다.
import hashlib, json, os, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "mck_pack")

# 1.21.9 이후 형식(min_format/max_format)과 예전 형식(pack_format/supported_formats)을 같이 적는다
meta = {"pack": {"description": "mck_pack", "pack_format": 34,
                 "supported_formats": {"min_inclusive": 34, "max_inclusive": 999},
                 "min_format": 34, "max_format": 999}}
with open(os.path.join(SRC, "pack.mcmeta"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)

files = []
for d, _, fs in os.walk(SRC):
    for n in fs:
        full = os.path.join(d, n)
        files.append((os.path.relpath(full, SRC).replace(os.sep, "/"), full))
files.sort()
zp = os.path.join(ROOT, "mck_pack.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for rel, full in files:
        zi = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        with open(full, "rb") as fh:
            z.writestr(zi, fh.read())
print("files:", len(files))
print("sha1:", hashlib.sha1(open(zp, "rb").read()).hexdigest())
