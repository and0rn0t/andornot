# andornot

Skript 스크립트(.sk) 저장소. 서버 `plugins/Skript/scripts` 폴더에 들어가는 파일들이 루트에 있어요.

- 인수인계 문서: `skill_core.sk` 맨 위 주석
- 파일은 GitHub에서 직접 고쳐도 돼요. Claude는 작업 전에 항상 최신 내용을 먼저 받아요.

## PC 자동 동기화 (사용자 PC 전용)
PC에는 저장소를 `git clone` 해 둔 폴더가 있고, 그 폴더 안의 `sync_local.bat`이 아래를 해요.
1. `git pull` 로 최신 파일을 받음
2. `.sk` 파일만 서버 스크립트 폴더에 복사 (다른 스크립트는 건드리지 않음)
3. 변경이 있으면 `sync.log`에 기록. 리로드는 직접 `/sk reload all`

- `sync_local.bat`은 PC마다 경로가 달라서 저장소에 올리지 않아요(`.gitignore`). 한글 폴더 경로가 있으면
  메모장에서 저장할 때 인코딩을 **ANSI**로 유지해야 해요.
- 직접 실행(더블클릭)하면 결과를 보여주고 멈춰요. 작업 스케줄러에서는 `/quiet`를 붙여 실행해요:
  `schtasks /create /sc minute /mo 1 /tn SkriptSync /tr "powershell -NoProfile -WindowStyle Hidden -Command \"& 'C:\skript_repo\sync_local.bat' /quiet\"" /f`
- `sync_to_server.bat`은 예전 버전이라 쓰지 않아요(저장소 파일은 PC에서 수정된 상태라 그대로 둠).

## 리소스 팩 (mck_pack)
배고픔 바 아이콘(`assets/minecraft/textures/gui/sprites/hud/food_*.png`)은 스태미너용 ⚡ 로 교체돼 있어요.
`resourcepack/mck_pack/`가 서버 리소스 팩 원본이에요(시작/라운드 시작 음악). `python3 resourcepack/build_pack.py`로 `resourcepack/mck_pack.zip`을 만들고 SHA-1을 출력해요.
`server.properties`에는 커밋 해시를 고정한 URL을 써요: `resource-pack=https://raw.githubusercontent.com/and0rn0t/andornot/<커밋 해시>/resourcepack/mck_pack.zip`, `resource-pack-sha1=<SHA-1>`.
