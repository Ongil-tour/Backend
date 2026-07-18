"""
TourAPI 세 개 오퍼레이션(detailCommon2/detailIntro2/detailWithTour2) 호출 결과를
facilities 테이블 한 row로 조립한다. 배치 스크립트(지역기반 목록 조회 → contentId 순회)의
재료 함수.
"""
from app.services.tour_api import (
    OPERATING_HOURS_FIELD_BY_TYPE,
    get_detail_common,
    get_detail_intro,
    get_detail_with_tour,
)


def _has_info(text: str | None) -> bool:
    """detailWithTour2 필드는 값 있으면 서술형 텍스트, 없으면 빈 문자열("")로 온다."""
    return bool(text and text.strip())


def assemble_facility(content_id: str, content_type_id: str, category: str | None = None) -> dict:
    """
    contentId 하나를 facilities upsert에 쓸 dict로 변환한다.
    이름/주소/좌표가 없는(detailCommon2 결과가 비어 있는) contentId는 호출 쪽에서
    걸러낼 수 있도록 ValueError를 던진다.
    """
    common = get_detail_common(content_id)
    if not common or "mapx" not in common or "mapy" not in common:
        raise ValueError(f"contentId={content_id}: detailCommon2에 좌표 정보 없음")

    intro = get_detail_intro(content_id, content_type_id)
    accessibility = get_detail_with_tour(content_id)

    operating_hours_field = OPERATING_HOURS_FIELD_BY_TYPE.get(content_type_id)
    operating_hours = intro.get(operating_hours_field) if operating_hours_field else None

    address = f"{common.get('addr1', '')} {common.get('addr2', '')}".strip()

    return {
        "content_id": content_id,
        "content_type_id": content_type_id,
        "name": common.get("title"),
        "category": category,
        "address": address or None,
        "lat": float(common["mapy"]),
        "lng": float(common["mapx"]),
        "operating_hours": operating_hours or None,
        "phone": common.get("tel") or None,
        # route=접근로(경사로/단차 서술), exit=주출입구(휠체어 접근 가능 서술).
        # 표본 확인 결과 값이 있을 때 전부 긍정 서술(부정 표현 없음)이라 non-empty=true로 판단.
        # wheelchair 필드는 접근성이 아니라 "휠체어 대여 가능 여부"라 매핑에서 제외.
        "wheelchair_accessible": _has_info(accessibility.get("exit")),
        "ramp": _has_info(accessibility.get("route")),
        "disabled_restroom": _has_info(accessibility.get("restroom")),
        "disabled_parking": _has_info(accessibility.get("parking")),
        "elevator": _has_info(accessibility.get("elevator")),
        "pet_friendly": _has_info(accessibility.get("helpdog")),
        "nursing_room": _has_info(accessibility.get("lactationroom")),
    }
