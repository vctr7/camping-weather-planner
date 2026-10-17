import asyncio
from time import monotonic

from app.regions import Region
from app.services.public_api import get_items, get_public_api_json
from app.settings import settings

API_URL = "https://apis.data.go.kr/B551011/GoCamping/basedList"
API_PAGE_SIZE = 1000
RESULT_PAGE_SIZE = 100
CACHE_TTL_SECONDS = 60 * 60
GWANGJU_DISTRICTS = {"광산구", "남구", "동구", "북구", "서구"}
PROVINCE_NAMES = {
    "seoul": {"서울특별시"},
    "incheon": {"인천광역시"},
    "daejeon": {"대전광역시"},
    "daegu": {"대구광역시"},
    "busan": {"부산광역시"},
    "ulsan": {"울산광역시"},
    "sejong": {"세종특별자치시"},
    "gyeonggi": {"경기도"},
    "gangneung": {"강원도", "강원특별자치도"},
    "chungbuk": {"충청북도"},
    "chungnam": {"충청남도"},
    "gyeongbuk": {"경상북도"},
    "gyeongnam": {"경상남도"},
    "jeonbuk": {"전라북도", "전북특별자치도"},
    "jeonnam": {"전라남도"},
    "jeju": {"제주특별자치도"},
}
_campground_cache: tuple[float, list[dict]] | None = None
_campground_cache_lock = asyncio.Lock()


async def search_campgrounds(
    region: Region, radius: int, camp_type: str | None, page: int
) -> dict:
    if not settings.camping_api_service_key:
        raise RuntimeError("CAMPING_API_SERVICE_KEY 환경변수를 설정해야 합니다.")

    source_items = await _get_all_campgrounds()
    camps = [
        _normalize_camp(item)
        for item in source_items
        if _belongs_to_region(item, region)
    ]
    if camp_type:
        camps = [
            camp
            for camp in camps
            if camp_type.casefold() in camp["type"].casefold()
        ]

    start = (page - 1) * RESULT_PAGE_SIZE
    return {
        "region": region.model_dump(),
        "items": camps[start : start + RESULT_PAGE_SIZE],
        "total_count": len(camps),
        "page": page,
    }


async def _get_all_campgrounds() -> list[dict]:
    global _campground_cache

    async with _campground_cache_lock:
        now = monotonic()
        if (
            _campground_cache
            and now - _campground_cache[0] < CACHE_TTL_SECONDS
        ):
            return _campground_cache[1]

        params: dict[str, str | int] = {
            "serviceKey": settings.camping_api_service_key,
            "numOfRows": API_PAGE_SIZE,
            "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "CampingWeatherPlanner",
            "_type": "json",
        }
        first_payload = await get_public_api_json(API_URL, params)
        body = first_payload.get("response", {}).get("body", {})
        items = get_items(first_payload)
        total_count = int(body.get("totalCount", len(items)))
        page_count = (total_count + API_PAGE_SIZE - 1) // API_PAGE_SIZE

        remaining_pages = await asyncio.gather(
            *(
                get_public_api_json(
                    API_URL,
                    {**params, "pageNo": page_no},
                )
                for page_no in range(2, page_count + 1)
            )
        )
        for payload in remaining_pages:
            items.extend(get_items(payload))

        _campground_cache = (monotonic(), items)
        return items


def _belongs_to_region(item: dict, region: Region) -> bool:
    province = str(item.get("doNm") or "").strip()
    district = str(item.get("sigunguNm") or "").strip()

    if province == "전남광주통합특별시":
        if region.id == "gwangju":
            return district in GWANGJU_DISTRICTS
        if region.id == "jeonnam":
            return district not in GWANGJU_DISTRICTS

    if region.id == "gwangju":
        return province == "광주광역시"
    if region.id == "jeonnam":
        return province in {"전라남도", "전남도"}
    return province in PROVINCE_NAMES.get(region.id, set())


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
