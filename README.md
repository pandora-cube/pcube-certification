![Pandoracube Certification](./verify/assets/pcube-certification.png)

# Pandoracube · Team Vent 스터디 인증

Pandoracube 동아리 내 공인 스터디의 수료 사실을 확인하는 정적 인증 페이지 모음입니다. 스터디 목록과 소개는 이 문서에서 제공하고, 인증 사이트는 개인별 인증 페이지만 제공합니다.

## 스터디 현황

### 2026년 진행

- [25-26 실시간 멀티플레이 스터디](./verify/realtime-multiplay-2026-01/info.md)

### 2025년 이전 진행

- 지속 추가 예정

## 인증 페이지 생성

수료자 정보는 각 스터디 디렉터리의 `data.json`에서 관리합니다. `study` 객체에는 스터디 ID(`id`), 이름(`name`), 공통 발급일(`issue_date`)을 입력하고, `recipients` 배열에는 수료자 이름만 입력합니다. 발급일은 `YYYY-MM-DD` 형식입니다. 배열 순서대로 `<study.id>-001`부터 발급번호가 부여되므로 기존 순서를 유지하고 새 수료자는 배열 끝에 추가합니다. 실제 수료자가 없는 스터디는 `recipients`를 빈 배열로 둡니다. 인증 배지는 스터디 디렉터리에 `badge.svg` 또는 `badge.png` 중 하나로 추가합니다. 수료자가 등록된 스터디에는 배지 파일이 정확히 하나 있어야 합니다. Pretendard 가변 폰트도 저장소에서 직접 제공하므로 인증 페이지는 외부 폰트 CDN 없이 표시됩니다. 폰트 라이선스는 `verify/assets/fonts/OFL.txt`에 포함했습니다. 생성용 HTML 템플릿은 `scripts/templates/`에, 사이트에서 제공하는 로고와 폰트는 `verify/assets/`에 있습니다.

저장소 루트에서 Python 3으로 생성기를 실행합니다.

```sh
python3 scripts/generate_certificates.py
```

특정 스터디만 생성하려면 디렉터리 이름을 지정합니다.

```sh
python3 scripts/generate_certificates.py --study realtime-multiplay-2026-01
```

각 수료자 페이지는 `verify/<스터디>/<발급번호>.html`에 생성됩니다. 예를 들어 발급번호가 `RMP-2026-001`이면 `verify/realtime-multiplay-2026-01/RMP-2026-001.html`입니다. 데이터를 수정한 뒤 생성된 페이지를 저장소에 커밋해 정적 호스팅에 배포합니다. 발급번호는 `study.id`와 `recipients` 배열 순서로 생성됩니다. 수료자 목록의 순서를 바꾸거나 중간 항목을 삭제하면 번호가 달라질 수 있으므로 기존 순서를 유지하고 새 이름은 끝에 추가해야 합니다. 인증을 철회할 때는 해당 발급번호의 `.html` 파일도 저장소에서 삭제합니다.

## 저작권

프로젝트는 2026년 Team Vent 내에서 개발되었습니다. 수료 데이터 및 이미지의 저작권은 세종대학교 판도라큐브 게임제작 동아리와 세종대학교 창업동아리 벤트에 있습니다.
