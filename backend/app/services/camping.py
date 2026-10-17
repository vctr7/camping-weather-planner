from app.regions import Region
from app.services.public_api import get_items, get_public_api_json
from app.settings import settings

API_URL = "https://apis.data.go.kr/B551011/GoCamping/locationBasedList"
AREA_API_URL = "https://apis.data.go.kr/B551011/GoCamping/areaBasedList"


async def search_campgrounds(
    region: Region, radius: int, camp_type: str | None, page: int
) -> dict:
    if not settings.camping_api_service_key:
        raise RuntimeError("CAMPING_API_SERVICE_KEY 환경변수를 설정해야 합니다.")

    params: dict[str, str | int] = {
        "serviceKey": settings.camping_api_service_key,
        "numOfRows": 100,
        "pageNo": page,
        "MobileOS": "ETC",
        "MobileApp": "CampingWeatherPlanner",
        "_type": "json",
    }
    if region.area_code:
        api_url = AREA_API_URL
        params["areaCode"] = region.area_code
    else:
        api_url = API_URL
        params.update(
            {
                "mapX": region.map_x,
                "mapY": region.map_y,
                "radius": radius,
            }
        )

    payload = await get_public_api_json(api_url, params)
    camps = [_normalize_camp(item) for item in get_items(payload)]
    if camp_type:
        camps = [
            camp
            for camp in camps
            if camp_type.casefold() in camp["type"].casefold()
        ]

    body = payload.get("response", {}).get("body", {})
    return {
        "region": region.model_dump(),
        "items": camps,
        "total_count": int(body.get("totalCount", len(camps))),
        "page": page,
    }


def _normalize_camp(item: dict) -> dict:
    return {
        "content_id": str(item.get("contentId", "")),
        "name": item.get("facltNm") or "이름 미등록 캠핑장",
        "address": item.get("addr1") or "",
        "province": item.get("doNm") or "",
        "district": item.get("sigunguNm") or "",
        "type": item.get("induty") or "",
        "facilities": [
            value.strip()
            for value in str(item.get("sbrsCl") or "").split(",")
            if value.strip()
        ],
        "pet_allowed": item.get("animalCmgCl") or "정보 없음",
        "reservation_url": item.get("resveUrl") or "",
        "image_url": item.get("firstImageUrl") or "",
        "map_x": item.get("mapX"),
        "map_y": item.get("mapY"),
        "tel": item.get("tel") or "",
        "description": item.get("lineIntro") or item.get("intro") or "",
    }
