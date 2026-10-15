# 커스텀 인증서 템플릿

스터디 폴더에 `template.html`을 두면 생성기가 기본 템플릿 대신 자동으로 사용합니다. 별도 명령 옵션은 필요하지 않습니다.

```text
verify/my-study/
├─ data.json
├─ badge.svg
└─ template.html
```

## 필수 치환자

호환성 검사는 아래 치환자가 모두 있는지 확인합니다. 하나라도 빠지거나 지원하지 않는 `{{...}}` 치환자가 있으면 생성을 중단하며 기존 출력은 수정하지 않습니다.

| 치환자 | 내용 |
| --- | --- |
| `{{EARNER_NAME}}` | 인증 대상자 이름 |
| `{{STUDY_NAME}}` | 스터디 이름 |
| `{{BADGE_ID}}` | 발급번호 |
| `{{ISSUE_DATE}}` | 발급일 |
| `{{CERTIFICATE_NAME}}` | `수료 인증` 또는 `운영 인증` |
| `{{HOLDER_ROLE}}` | `수료자` 또는 `운영자` |

선택 치환자는 `{{CERTIFICATE_TYPE}}`(`recipient` 또는 `operator`), `{{CANONICAL_URL}}`, `{{OG_IMAGE_URL}}`, `{{LINKEDIN_URL}}`, `{{BADGE_IMAGE_URL}}`, `{{BACKGROUND_IMAGE_URL}}`, `{{STAMP_IMAGE_URL}}`, `{{CERTIFICATION_LOGO_URL}}`입니다.

치환값은 HTML 속성에서도 안전하도록 이스케이프됩니다. 이미지 치환자는 상대경로가 아니라 data URI로 들어가므로 생성된 인증서 HTML 하나만 옮겨도 표시됩니다. `BACKGROUND_IMAGE_URL`은 CSS `background-image` 값 전체(`none` 또는 `url(...)`)입니다.

## 최소 예제

```html
<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>{{STUDY_NAME}} {{CERTIFICATE_NAME}}</title></head>
<body data-certificate-type="{{CERTIFICATE_TYPE}}">
  <img src="{{BADGE_IMAGE_URL}}" alt="">
  <h1>{{STUDY_NAME}} {{CERTIFICATE_NAME}}</h1>
  <p>{{EARNER_NAME}} · {{HOLDER_ROLE}}</p>
  <p>{{BADGE_ID}} / {{ISSUE_DATE}}</p>
</body>
</html>
```

## 전체 호환 기능 유지

LinkedIn 등록, iframe 복사, 임베드 전용 화면, canonical/Open Graph까지 모두 유지하려면 `scripts/templates/certificate.html`을 복사해 디자인만 수정하는 방식을 권장합니다. 특히 다음 요소를 유지해야 합니다.

- `{{LINKEDIN_URL}}` 링크
- `body`의 공개 URL·이름·인증 종류 `data-*` 속성
- `copy-embed`, `copy-status` 요소와 복사 스크립트
- `?embed=1`을 처리하는 스크립트와 `html[data-embed="true"]` 스타일
- `{{CANONICAL_URL}}`, `{{OG_IMAGE_URL}}` 메타데이터

템플릿을 추가한 뒤 다음 명령으로 호환성과 결과를 확인합니다.

```sh
python3 scripts/generate_certificates.py --study my-study
```

오류가 나면 기본 템플릿으로 자동 대체하지 않습니다. 메시지에 표시된 누락 또는 미지원 치환자를 고친 뒤 다시 생성해야 합니다.
