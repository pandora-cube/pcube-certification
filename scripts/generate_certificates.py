#!/usr/bin/env python3
"""Generate static certificate pages from study data files."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VERIFY_DIR = ROOT / "verify"
TEMPLATE_PATH = ROOT / "scripts/templates/certificate.html"
LANDING_TEMPLATE_PATH = ROOT / "scripts/templates/index.html"
REDIRECT_TEMPLATE_PATH = ROOT / "scripts/templates/redirect.html"
CONFIG_PATH = ROOT / "certification.config.json"
PUBLIC_ASSETS = Path("verify/assets")
STAMP_ASSET = PUBLIC_ASSETS / "pcube-symbol.png"
CERTIFICATION_LOGO_ASSET = PUBLIC_ASSETS / "pcube-certification.png"
REQUIRED_STUDY_FIELDS = ("id", "name", "issue_date")
STUDY_BADGE_FILENAMES = ("badge.svg", "badge.png")
STUDY_TEMPLATE_FILENAME = "template.html"
SAFE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")
RAW_PLACEHOLDER_PATTERN = re.compile(r"\{\{([^{}]+)\}\}")
REQUIRED_TEMPLATE_PLACEHOLDERS = {
    "EARNER_NAME",
    "STUDY_NAME",
    "BADGE_ID",
    "ISSUE_DATE",
    "CERTIFICATE_NAME",
    "HOLDER_ROLE",
}
ALLOWED_TEMPLATE_PLACEHOLDERS = REQUIRED_TEMPLATE_PLACEHOLDERS | {
    "CERTIFICATE_TYPE",
    "CANONICAL_URL",
    "OG_IMAGE_URL",
    "LINKEDIN_URL",
    "BADGE_IMAGE_URL",
    "BACKGROUND_IMAGE_URL",
    "STAMP_IMAGE_URL",
    "CERTIFICATION_LOGO_URL",
}
IMAGE_MIME_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def load_data(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path.relative_to(ROOT)}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: 최상위 값은 객체여야 합니다.")
    return data


def require_text_fields(value: dict, fields: tuple[str, ...], context: str) -> None:
    for field in fields:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"{context}: '{field}'는 비어 있지 않은 문자열이어야 합니다.")


def safe_component(value: str, context: str) -> str:
    if not SAFE_PATH_COMPONENT.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"{context}: 경로에 사용할 수 없는 값입니다: {value!r}")
    return value


def repository_asset(asset: str) -> Path:
    """Resolve and validate an asset path inside the repository."""
    asset_path = Path(asset)
    if asset_path.is_absolute() or ".." in asset_path.parts:
        raise ValueError(f"이미지 경로는 저장소 내부의 상대 경로여야 합니다: {asset!r}")
    target = (ROOT / asset_path).resolve()
    if ROOT.resolve() not in target.parents:
        raise ValueError(f"이미지 경로는 저장소 내부여야 합니다: {asset!r}")
    if not target.is_file():
        raise ValueError(f"이미지 파일을 찾을 수 없습니다: {asset!r}")
    return target


def image_data_uri(asset: str) -> str:
    """Encode an image as a self-contained data URI."""
    target = repository_asset(asset)
    mime_type = IMAGE_MIME_TYPES.get(target.suffix.lower())
    if not mime_type:
        supported = ", ".join(sorted(IMAGE_MIME_TYPES))
        raise ValueError(f"지원하지 않는 이미지 형식입니다: {asset!r} (지원: {supported})")
    encoded = base64.b64encode(target.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def load_public_base_url() -> str:
    config = load_data(CONFIG_PATH)
    public_base_url = config.get("public_base_url")
    if not isinstance(public_base_url, str) or not public_base_url.strip():
        raise ValueError(f"{CONFIG_PATH.name}: 'public_base_url'에 실제 공개 URL을 입력해야 합니다.")
    public_base_url = public_base_url.strip().rstrip("/")
    parsed = urlsplit(public_base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError(
            f"{CONFIG_PATH.name}: 'public_base_url'은 경로·쿼리·프래그먼트가 없는 HTTPS URL이어야 합니다."
        )
    return public_base_url


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", escape(value, quote=True))
    unresolved = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if unresolved:
        raise ValueError("템플릿에 처리되지 않은 치환자가 있습니다: " + ", ".join(sorted(set(unresolved))))
    return template


def validate_template(template: str, template_path: Path) -> None:
    placeholders = set(PLACEHOLDER_PATTERN.findall(template))
    raw_placeholders = {value.strip() for value in RAW_PLACEHOLDER_PATTERN.findall(template)}
    missing = sorted(REQUIRED_TEMPLATE_PLACEHOLDERS - placeholders)
    unsupported = sorted(raw_placeholders - ALLOWED_TEMPLATE_PLACEHOLDERS)
    errors = []
    if missing:
        errors.append("필수 치환자 누락: " + ", ".join("{{" + value + "}}" for value in missing))
    if unsupported:
        errors.append("지원하지 않는 치환자: " + ", ".join("{{" + value + "}}" for value in unsupported))
    if errors:
        try:
            display_path = template_path.relative_to(ROOT)
        except ValueError:
            display_path = template_path
        raise ValueError(f"{display_path}: 템플릿이 호환되지 않습니다. " + " / ".join(errors))


def validate_people(value: object, field: str, data_path: Path) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{data_path.relative_to(ROOT)}: '{field}' 배열이 필요합니다.")
    people = []
    for index, person in enumerate(value):
        if not isinstance(person, str) or not person.strip():
            raise ValueError(
                f"{data_path.relative_to(ROOT)}: {field}[{index}]는 비어 있지 않은 이름 문자열이어야 합니다."
            )
        people.append(person)
    return people


def generate_study(data_path: Path, default_template: str, public_base_url: str) -> tuple[int, int]:
    data = load_data(data_path)
    study = data.get("study")
    if not isinstance(study, dict):
        raise ValueError(f"{data_path.relative_to(ROOT)}: 'study' 객체가 필요합니다.")
    require_text_fields(study, REQUIRED_STUDY_FIELDS, "study")
    recipients = validate_people(data.get("recipients"), "recipients", data_path)
    operators = validate_people(data.get("operators", []), "operators", data_path)

    study_dir = data_path.parent
    safe_component(study_dir.name, "스터디 디렉터리")
    study_id = safe_component(study["id"], "study.id")
    try:
        if date.fromisoformat(study["issue_date"]).isoformat() != study["issue_date"]:
            raise ValueError
    except ValueError as error:
        raise ValueError("study.issue_date: 날짜는 YYYY-MM-DD 형식이어야 합니다.") from error

    custom_template_path = study_dir / STUDY_TEMPLATE_FILENAME
    template_path = custom_template_path if custom_template_path.is_file() else TEMPLATE_PATH
    template = custom_template_path.read_text(encoding="utf-8") if custom_template_path.is_file() else default_template
    validate_template(template, template_path)

    badge_files = [study_dir / name for name in STUDY_BADGE_FILENAMES if (study_dir / name).is_file()]
    if (recipients or operators) and len(badge_files) != 1:
        expected = " 또는 ".join(STUDY_BADGE_FILENAMES)
        raise ValueError(
            f"{study_dir.relative_to(ROOT)}: 인증 대상자가 있으면 {expected} 중 하나만 있어야 합니다. "
            f"현재 발견: {len(badge_files)}개"
        )
    badge_asset = badge_files[0] if badge_files else None
    badge_path = badge_asset.relative_to(ROOT).as_posix() if badge_asset else ""
    badge_image = image_data_uri(badge_path) if badge_path else ""
    background = study.get("background_image", "")
    if not isinstance(background, str):
        raise ValueError("study.background_image: 문자열이어야 합니다.")
    background_image = f"url({image_data_uri(background)})" if background else "none"
    asset_urls = {
        "BADGE_IMAGE_URL": badge_image,
        "BACKGROUND_IMAGE_URL": background_image,
        "STAMP_IMAGE_URL": image_data_uri(STAMP_ASSET.as_posix()),
        "CERTIFICATION_LOGO_URL": image_data_uri(CERTIFICATION_LOGO_ASSET.as_posix()),
    }
    issue_date = date.fromisoformat(study["issue_date"])
    study_slug = study_dir.name
    redirect_template = REDIRECT_TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered_pages: list[tuple[Path, str]] = []
    roles = (
        ("recipient", "수료 인증", "수료자", recipients, ""),
        ("operator", "운영 인증", "운영자", operators, "-OP"),
    )
    for certificate_type, certificate_name, holder_role, people, id_suffix in roles:
        for index, person in enumerate(people, start=1):
            badge_id = f"{study_id}{id_suffix}-{index:03d}"
            credential_url = f"{public_base_url}/{quote(study_slug)}/{quote(badge_id)}.html"
            og_image_url = f"{public_base_url}/{quote(study_slug)}/{quote(badge_asset.name)}"
            linkedin_url = "https://www.linkedin.com/profile/add?" + urlencode(
                {
                    "startTask": "CERTIFICATION_NAME",
                    "name": f"{study['name']} {certificate_name}",
                    "organizationName": "Pandoracube · Team Vent",
                    "issueYear": issue_date.year,
                    "issueMonth": issue_date.month,
                    "certUrl": credential_url,
                    "certId": badge_id,
                }
            )
            values = {
                "EARNER_NAME": person,
                "STUDY_NAME": study["name"],
                "BADGE_ID": badge_id,
                "ISSUE_DATE": study["issue_date"],
                "CERTIFICATE_TYPE": certificate_type,
                "CERTIFICATE_NAME": certificate_name,
                "HOLDER_ROLE": holder_role,
                "CANONICAL_URL": credential_url,
                "OG_IMAGE_URL": og_image_url,
                "LINKEDIN_URL": linkedin_url,
                **asset_urls,
            }
            rendered_pages.append((study_dir / f"{badge_id}.html", render(template, values)))
            rendered_pages.append(
                (
                    study_dir / badge_id / "index.html",
                    render(redirect_template, {"CANONICAL_URL": credential_url}),
                )
            )

    for output_path, content in rendered_pages:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    return len(recipients), len(operators)


def generate_landing_page(public_base_url: str) -> None:
    template = LANDING_TEMPLATE_PATH.read_text(encoding="utf-8")
    values = {
        "CANONICAL_URL": public_base_url + "/",
        "OG_IMAGE_URL": public_base_url + "/assets/pcube-certification.png",
        "CERTIFICATION_LOGO_URL": image_data_uri(CERTIFICATION_LOGO_ASSET.as_posix()),
    }
    (VERIFY_DIR / "index.html").write_text(render(template, values), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="스터디 인증 HTML 페이지를 생성합니다.")
    parser.add_argument("--study", required=True, help="verify 아래에서 생성할 스터디 디렉터리 이름")
    args = parser.parse_args()

    try:
        study_slug = safe_component(args.study, "스터디 디렉터리")
    except ValueError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1
    data_path = VERIFY_DIR / study_slug / "data.json"

    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        validate_template(template, TEMPLATE_PATH)
        public_base_url = load_public_base_url()
        if not data_path.is_file():
            raise ValueError(f"데이터 파일을 찾을 수 없습니다: {data_path.relative_to(ROOT)}")
        recipient_count, operator_count = generate_study(data_path, template, public_base_url)
        generate_landing_page(public_base_url)
    except (OSError, ValueError) as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1
    print(
        f"{data_path.parent.relative_to(ROOT)}: "
        f"수료 인증 {recipient_count}개, 운영 인증 {operator_count}개 생성"
    )
    print("랜딩 페이지와 기존 URL 호환 경로 생성 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
