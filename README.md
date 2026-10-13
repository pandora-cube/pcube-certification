![Pandoracube Certification](./verify/pcube-certification.png)

# Pandoracube · Team Vent 스터디 인증

Pandoracube 동아리 내 공인 스터디의 수료 사실을 확인하는 정적 인증 페이지 모음입니다. 스터디 목록과 소개는 이 문서에서 제공하고, 인증 사이트는 개인별 인증 페이지만 제공합니다.

## 스터디 현황

### 2026년 진행

- [25-26 실시간 멀티플레이 스터디](./verify/realtime-multiplay-2026-01/info.md)

### 2025년 이전 진행

- 지속 추가 예정

## 인증 페이지 생성

수료자 정보는 각 스터디 디렉터리의 `data.json`에서 관리합니다. 필드는 `study.name`과 `recipients` 배열의 `name`, `badge_id`, `issue_date`입니다. 날짜는 `YYYY-MM-DD` 형식으로 입력합니다. 실제 수료자 정보가 없는 스터디는 `recipients`를 빈 배열로 둡니다. 인증 배지는 스터디 디렉터리에 `badge.svg` 또는 `badge.png` 중 하나로 추가합니다. 수료자가 등록된 스터디에는 배지 파일이 정확히 하나 있어야 합니다. Pretendard 가변 폰트도 저장소에서 직접 제공하므로 인증 페이지는 외부 폰트 CDN 없이 표시됩니다. 폰트 라이선스는 `verify/fonts/OFL.txt`에 포함했습니다.

저장소 루트에서 Python 3으로 생성기를 실행합니다.

```sh
python3 scripts/generate_certificates.py
```

특정 스터디만 생성하려면 디렉터리 이름을 지정합니다.

```sh
python3 scripts/generate_certificates.py --study realtime-multiplay-2026-01
```

각 수료자 페이지는 `verify/<스터디>/<발급번호>/index.html`에 생성됩니다. 데이터를 수정한 뒤 생성된 페이지를 저장소에 커밋해 정적 호스팅에 배포합니다. 발급번호는 URL 경로로 사용하므로 영문자, 숫자, 점, 밑줄, 하이픈만 허용하며 스터디 내에서 중복될 수 없습니다. 발급번호가 있는 페이지를 철회할 때는 해당 발급번호 디렉터리도 저장소에서 삭제해야 합니다.

## 저작권

프로젝트는 2026년 Team Vent 내에서 개발되었습니다. 수료 데이터 및 이미지의 저작권은 세종대학교 판도라큐브 게임제작 동아리와 세종대학교 창업동아리 벤트에 있습니다.
