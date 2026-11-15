# andornot

Skript 스크립트(.sk) 저장소. 서버 `plugins/Skript/scripts` 폴더에 들어가는 파일들이 루트에 있어요.

- 인수인계 문서: `skill_core.sk` 맨 위 주석
- `sync_to_server.bat`: 저장소를 받아서(`git pull`) 서버 스크립트 폴더에 `.sk` 파일만 복사해요. 변경이 있으면 `sync.log`에 기록해요. 리로드는 직접 `/sk reload all`.

## PC 설정 (한 번만)
1. git 설치: https://git-scm.com/download/win
2. 원하는 위치에 저장소를 받기: `git clone https://github.com/and0rn0t/andornot C:\skript_repo`
   (비공개 저장소면 처음에 GitHub 로그인 창이 떠요)
3. `C:\skript_repo\sync_to_server.bat`을 메모장으로 열어 `SCRIPTS_DIR` 줄을 서버의 `plugins\Skript\scripts` 경로로 수정
4. 더블클릭해서 한 번 실행해 보기 (스크립트 폴더에 파일이 복사되는지 확인)
5. 1분마다 자동 실행 등록 (명령 프롬프트):
   `schtasks /create /sc minute /mo 1 /tn SkriptSync /tr "powershell -NoProfile -WindowStyle Hidden -Command \"& 'C:\skript_repo\sync_to_server.bat'\"" /f`
