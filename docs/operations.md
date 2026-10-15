# 인증 사이트 운영

## 스터디 데이터

스터디마다 `verify/<study>/` 폴더를 만들고 다음 파일을 둡니다.

```text
verify/<study>/
├─ data.json
├─ badge.svg 또는 badge.png
└─ template.html (선택)
```

`data.json` 예시는 다음과 같습니다.

```json
{
  "study": {
    "id": "RMP-2026",
    "name": "25-26 실시간 멀티플레이 스터디",
    "issue_date": "2026-03-03"
  },
  "recipients": ["홍길동"],
  "operators": ["김운영"]
}
```

- `recipients`: 수료자 명단이며 발급번호는 `<study.id>-001` 형식입니다.
- `operators`: 운영자 명단이며 발급번호는 `<study.id>-OP-001` 형식입니다. 생략하면 빈 배열로 처리됩니다.
- 명단 순서가 발급번호를 결정하므로 기존 인원 순서는 유지하고 새 인원은 끝에 추가합니다.
- 인증 대상자가 있으면 `badge.svg`와 `badge.png` 중 정확히 하나가 필요합니다.
- `issue_date`는 `YYYY-MM-DD` 형식입니다.

`template.html`이 있으면 해당 스터디에만 자동 적용됩니다. 없으면 LinkedIn 등록, iframe 임베드, Open Graph, 단일 HTML 이미지 내장을 지원하는 기본 템플릿을 사용합니다. 자세한 규격은 [커스텀 인증서 템플릿](custom-template.md)을 참고하세요.

## 공개 URL 설정

`certification.config.json`의 `public_base_url`에 경로 없는 실제 HTTPS 도메인을 입력합니다.

```json
{
  "public_base_url": "https://certificate.p-cube.kr"
}
```

이 값은 LinkedIn 자격증 URL, iframe 주소, canonical URL과 Open Graph 메타데이터에 사용됩니다.

## 로컬 생성

생성기는 스터디 하나를 명시적으로 처리합니다.

```sh
python3 scripts/generate_certificates.py --study realtime-multiplay-2026-01
```

공식 인증서는 `verify/<study>/<발급번호>.html`, 확장자 없는 기존 URL을 위한 이동 페이지는 `verify/<study>/<발급번호>/index.html`에 생성됩니다. 사이트 랜딩 페이지도 `verify/index.html`에 생성됩니다. 이 산출물은 Git에서 추적하지 않으며 `data.json`, 배지, 선택적 `template.html`이 원본입니다.

## LinkedIn 및 임베드

기본 템플릿의 **LinkedIn에 등록** 버튼은 스터디명, 인증 종류, 발급 연월, 발급번호와 공식 URL을 LinkedIn 등록 화면에 전달합니다. 발급 기관은 사용자가 `Pandoracube · Team Vent`로 선택합니다.

**임베드 코드 복사** 버튼은 같은 인증 URL에 `?embed=1`을 붙인 iframe 코드를 복사합니다. 배포 환경에서 `X-Frame-Options` 또는 Content Security Policy의 `frame-ancestors`로 외부 표시를 차단하지 않아야 합니다.
