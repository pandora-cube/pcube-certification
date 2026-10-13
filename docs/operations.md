# 인증 사이트 운영

## 수료 데이터 작성

수료자 정보는 각 스터디 디렉터리의 `data.json`에서 관리합니다. `study` 객체에는 스터디 ID(`id`), 이름(`name`), 공통 발급일(`issue_date`)을 입력하고, `recipients` 배열에는 수료자 이름만 입력합니다. 발급일은 `YYYY-MM-DD` 형식입니다. 배열 순서대로 `<study.id>-001`부터 발급번호가 부여되므로 기존 순서를 유지하고 새 수료자는 배열 끝에 추가합니다. 수료자가 없는 스터디는 `recipients`를 빈 배열로 둡니다.

수료자가 등록된 스터디 디렉터리에는 `badge.svg` 또는 `badge.png` 중 하나를 둡니다. 생성기는 둘 중 정확히 하나가 있는지 확인합니다. Pretendard 가변 폰트와 서비스 로고는 `verify/assets/`에서 제공합니다. 폰트 라이선스는 `verify/assets/fonts/OFL.txt`에 있습니다. 인증 HTML 템플릿은 `scripts/templates/`에서 관리합니다.

## 인증 페이지 생성

저장소 루트에서 모든 스터디 페이지를 생성합니다.

```sh
python3 scripts/generate_certificates.py
```

특정 스터디만 생성할 수 있습니다.

```sh
python3 scripts/generate_certificates.py --study realtime-multiplay-2026-01
```

인증 페이지는 `verify/<스터디>/<발급번호>.html`에 생성됩니다. 예를 들어 `RMP-2026-001` 페이지는 `verify/realtime-multiplay-2026-01/RMP-2026-001.html`입니다. 생성된 HTML과 `verify/_redirects`를 함께 커밋해 배포합니다. 인증을 철회할 때는 해당 HTML 파일도 저장소에서 삭제합니다.

## Cloudflare Pages

Pages 프로젝트의 루트 디렉터리는 저장소 루트로, 빌드 출력 디렉터리는 `verify`로 설정합니다. 별도 빌드 명령은 사용하지 않습니다. 생성된 `verify/_redirects`는 등록된 인증 URL `/<스터디>/<발급번호>`를 대응하는 `.html` 파일에 내부 연결합니다. 규칙은 데이터에 등록되어 있고 HTML 파일도 존재하는 인증에 대해서만 생성됩니다. 따라서 수료 데이터를 수정한 후 페이지를 다시 생성하고 변경된 HTML과 `_redirects`를 커밋해야 합니다.

서브도메인은 Cloudflare Pages 프로젝트의 **Custom domains**에서 연결합니다. 사이트 최상위 경로(`/`)에는 페이지를 제공하지 않습니다. 스터디 소개 페이지가 필요해지면 해당 스터디 경로에 페이지를 추가합니다.
