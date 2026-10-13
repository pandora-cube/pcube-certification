#!/usr/bin/env python3
"""Generate static certificate pages from study data files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
VERIFY_DIR = ROOT / "verify"
TEMPLATE_PATH = ROOT / "scripts/templates/certificate.html"
PUBLIC_ASSETS = Path("verify/assets")
FONT_ASSET = PUBLIC_ASSETS / "fonts/PretendardVariable.ttf"
STAMP_ASSET = PUBLIC_ASSETS / "pcube-symbol.png"
CERTIFICATION_LOGO_ASSET = PUBLIC_ASSETS / "pcube-certification.png"
REQUIRED_STUDY_FIELDS = ("id", "name", "issue_date")
STUDY_BADGE_FILENAMES = ("badge.svg", "badge.png")
SAFE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


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


def relative_asset(asset: str, page_dir: Path) -> str:
    """Return an escaped URL from a generated page to a repository asset."""
    asset_path = Path(asset)
    if asset_path.is_absolute() or ".." in asset_path.parts:
        raise ValueError(f"이미지 경로는 저장소 내부의 상대 경로여야 합니다: {asset!r}")
    target = ROOT / asset_path
    if not target.is_file():
        raise ValueError(f"이미지 파일을 찾을 수 없습니다: {asset!r}")
    relative = Path(os.path.relpath(target, page_dir))
    return quote(relative.as_posix(), safe="/.-_~")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", escape(value, quote=True))
    unresolved = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if unresolved:
        raise ValueError("템플릿에 처리되지 않은 치환자가 있습니다: " + ", ".join(sorted(set(unresolved))))
    return template


def generate_study(data_path: Path, template: str) -> int:
    data = load_data(data_path)
    study = data.get("study")
    recipients = data.get("recipients")
    if not isinstance(study, dict):
        raise ValueError(f"{data_path.relative_to(ROOT)}: 'study' 객체가 필요합니다.")
    if not isinstance(recipients, list):
        raise ValueError(f"{data_path.relative_to(ROOT)}: 'recipients' 배열이 필요합니다.")
    require_text_fields(study, REQUIRED_STUDY_FIELDS, "study")

    study_dir = data_path.parent
    safe_component(study_dir.name, "스터디 디렉터리")
    study_id = safe_component(study["id"], "study.id")
    try:
        if date.fromisoformat(study["issue_date"]).isoformat() != study["issue_date"]:
            raise ValueError
    except ValueError as error:
        raise ValueError("study.issue_date: 날짜는 YYYY-MM-DD 형식이어야 합니다.") from error

    badge_files = [study_dir / name for name in STUDY_BADGE_FILENAMES if (study_dir / name).is_file()]
    if recipients and len(badge_files) != 1:
        expected = " 또는 ".join(STUDY_BADGE_FILENAMES)
        raise ValueError(
            f"{study_dir.relative_to(ROOT)}: 수료자가 있으면 {expected} 중 하나만 있어야 합니다. "
            f"현재 발견: {len(badge_files)}개"
        )
    badge_asset = badge_files[0] if badge_files else None
    badge_image = relative_asset(badge_asset.relative_to(ROOT).as_posix(), study_dir) if badge_asset else ""
    background = study.get("background_image", "")
    background_image = f"url({relative_asset(background, study_dir)})" if background else "none"
    asset_urls = {
        "BADGE_IMAGE_URL": badge_image,
        "BACKGROUND_IMAGE_URL": background_image,
        "FONT_URL": relative_asset(FONT_ASSET.as_posix(), study_dir),
        "STAMP_IMAGE_URL": relative_asset(STAMP_ASSET.as_posix(), study_dir),
        "CERTIFICATION_LOGO_URL": relative_asset(CERTIFICATION_LOGO_ASSET.as_posix(), study_dir),
    }
    for index, recipient in enumerate(recipients, start=1):
        context = f"recipients[{index - 1}]"
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError(f"{context}: 비어 있지 않은 이름 문자열이어야 합니다.")
        badge_id = f"{study_id}-{index:03d}"

        output_path = study_dir / f"{badge_id}.html"
        values = {
            "EARNER_NAME": recipient,
            "STUDY_NAME": study["name"],
            "BADGE_ID": badge_id,
            "ISSUE_DATE": study["issue_date"],
            **asset_urls,
        }
        output_path.write_text(render(template, values), encoding="utf-8")
    return len(recipients)


def main() -> int:
    parser = argparse.ArgumentParser(description="스터디 수료 인증 HTML 페이지를 생성합니다.")
    parser.add_argument("--study", help="verify 아래 스터디 디렉터리 이름 (기본값: 모든 data.json 처리)")
    args = parser.parse_args()

    try:
        study_slug = safe_component(args.study, "스터디 디렉터리") if args.study else None
    except ValueError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1
    data_files = [VERIFY_DIR / study_slug / "data.json"] if study_slug else sorted(VERIFY_DIR.glob("*/data.json"))
    if not data_files:
        print("처리할 스터디 data.json이 없습니다.", file=sys.stderr)
        return 1

    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        total = 0
        for data_path in data_files:
            if not data_path.is_file():
                raise ValueError(f"데이터 파일을 찾을 수 없습니다: {data_path.relative_to(ROOT)}")
            count = generate_study(data_path, template)
            print(f"{data_path.parent.relative_to(ROOT)}: {count}개 페이지 생성")
            total += count
    except (OSError, ValueError) as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1
    print(f"완료: 총 {total}개 페이지")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
