from datetime import date, datetime, timedelta
from math import cos, floor, log, pi, sin, tan
from zoneinfo import ZoneInfo

from app.regions import Region
from app.services.public_api import get_items, get_public_api_json
from app.settings import settings

VILLAGE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
LAND_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"
TEMPERATURE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
KOREA = ZoneInfo("Asia/Seoul")


async def get_weather_forecast(
    region: Region,
    target_date: date,
    map_x: float | None = None,
    map_y: float | None = None,
) -> dict:
    if not settings.weather_api_service_key:
        raise RuntimeError("WEATHER_API_SERVICE_KEY 환경변수를 설정해야 합니다.")

    today = datetime.now(KOREA).date()
    forecast_day = (target_date - today).days
    if map_x is not None and map_y is not None and 0 <= forecast_day <= 3:
        nx, ny = _grid_coordinates(map_x, map_y)
        return await _get_village_forecast(
            region, target_date, forecast_day, nx, ny
        )

    return await _get_regional_forecast(region, target_date)


async def _get_village_forecast(
    region: Region, target_date: date, forecast_day: int, nx: int, ny: int
) -> dict:
    now = datetime.now(KOREA)
    issue_time = _latest_village_issue_time(now)
    payload = await get_public_api_json(
        VILLAGE_URL,
        {
            "serviceKey": settings.weather_api_service_key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
            "base_date": issue_time.strftime("%Y%m%d"),
            "base_time": issue_time.strftime("%H%M"),
            "nx": nx,
            "ny": ny,
        },
    )
    items = [
        item
        for item in get_items(payload)
        if item.get("fcstDate") == target_date.strftime("%Y%m%d")
    ]
    if not items:
        raise RuntimeError("기상청에서 캠핑장 인근 상세예보를 찾지 못했습니다.")

    values: dict[str, list[str]] = {}
    for item in items:
        values.setdefault(str(item.get("category", "")), []).append(
            str(item.get("fcstValue", ""))
        )

    temperatures = _numeric_values(values.get("TMP", []))
    precipitation = _numeric_values(values.get("POP", []))
    weather = _village_weather(values)
    min_temperature = _first_numeric(values.get("TMN", []))
    max_temperature = _first_numeric(values.get("TMX", []))
    return {
        "region": region.model_dump(),
        "date": target_date.isoformat(),
        "forecast_day": forecast_day,
        "issued_at": issue_time.isoformat(),
        "precipitation_probability": (
            round(sum(precipitation) / len(precipitation))
            if precipitation
            else None
        ),
        "weather": weather,
        "min_temperature": (
            min_temperature
            if min_temperature is not None
            else min(temperatures) if temperatures else None
        ),
        "max_temperature": (
            max_temperature
            if max_temperature is not None
            else max(temperatures) if temperatures else None
        ),
        "forecast_scope": "campground",
        "location_name": "캠핑장 인근",
    }


async def _get_regional_forecast(region: Region, target_date: date) -> dict:
    issue_time = _latest_issue_time()
    forecast_day = (target_date - issue_time.date()).days
    if not 3 <= forecast_day <= 10:
        raise ValueError("중기예보는 발표일 기준 3~10일 뒤 날짜만 조회할 수 있습니다.")

    common = {
        "serviceKey": settings.weather_api_service_key,
        "pageNo": 1,
        "numOfRows": 10,
        "dataType": "JSON",
        "regId": region.land_reg_id,
        "tmFc": issue_time.strftime("%Y%m%d%H%M"),
    }
    land_payload = await get_public_api_json(LAND_URL, common)
    temperature_payload = await get_public_api_json(
        TEMPERATURE_URL,
        {
            **common,
            "regId": region.temperature_reg_id,
        },
    )
    land_items = get_items(land_payload)
    temperature_items = get_items(temperature_payload)
    if not land_items or not temperature_items:
        raise RuntimeError("기상청 API에서 해당 지역의 예보 데이터를 찾지 못했습니다.")

    land = land_items[0]
    temperature = temperature_items[0]
    return {
        "region": region.model_dump(),
        "date": target_date.isoformat(),
        "forecast_day": forecast_day,
        "issued_at": issue_time.isoformat(),
        "precipitation_probability": _period_average(
            land, f"rnSt{forecast_day}", suffixes=("Am", "Pm")
        ),
        "weather": _weather_description(
            land, f"wf{forecast_day}", suffixes=("Am", "Pm")
        ),
        "min_temperature": temperature.get(f"taMin{forecast_day}"),
        "max_temperature": temperature.get(f"taMax{forecast_day}"),
        "forecast_scope": "region",
        "location_name": region.name,
    }


def _latest_village_issue_time(now: datetime) -> datetime:
    issue_times = (2, 5, 8, 11, 14, 17, 20, 23)
    available_before = now - timedelta(minutes=50)
    issue_date = available_before.date()
    candidates = [
        datetime.combine(issue_date, datetime.min.time(), KOREA).replace(hour=hour)
        for hour in issue_times
    ]
    eligible = [candidate for candidate in candidates if candidate <= available_before]
    if eligible:
        return eligible[-1]
    issue_date -= timedelta(days=1)
    return datetime.combine(issue_date, datetime.min.time(), KOREA).replace(hour=23)


def _grid_coordinates(longitude: float, latitude: float) -> tuple[int, int]:
    earth_radius = 6371.00877 / 5.0
    lat1 = 30.0 * pi / 180.0
    lat2 = 60.0 * pi / 180.0
    origin_lon = 126.0 * pi / 180.0
    origin_lat = 38.0 * pi / 180.0
    scale_x = 43
    scale_y = 136

    sn = log(cos(lat1) / cos(lat2)) / log(
        tan(pi / 4.0 + lat2 / 2.0) / tan(pi / 4.0 + lat1 / 2.0)
    )
    sf = tan(pi / 4.0 + lat1 / 2.0) ** sn * cos(lat1) / sn
    ro = earth_radius * sf / tan(pi / 4.0 + origin_lat / 2.0) ** sn

    lat = latitude * pi / 180.0
    lon = longitude * pi / 180.0
    ra = earth_radius * sf / tan(pi / 4.0 + lat / 2.0) ** sn
    theta = lon - origin_lon
    if theta > pi:
        theta -= 2.0 * pi
    if theta < -pi:
        theta += 2.0 * pi
    theta *= sn

    nx = floor(ra * sin(theta) + scale_x + 0.5)
    ny = floor(ro - ra * cos(theta) + scale_y + 0.5)
    return nx, ny


def _numeric_values(values: list[str]) -> list[float]:
    result: list[float] = []
    for value in values:
        try:
            result.append(float(value))
        except ValueError:
            continue
    return result


def _first_numeric(values: list[str]) -> float | None:
    parsed = _numeric_values(values)
    return parsed[0] if parsed else None


def _village_weather(values: dict[str, list[str]]) -> str:
    precipitation_types = {
        "1": "비",
        "2": "비 또는 눈",
        "3": "눈",
        "4": "소나기",
    }
    precipitation = list(
        dict.fromkeys(
            precipitation_types[value]
            for value in values.get("PTY", [])
            if value in precipitation_types
        )
    )
    if precipitation:
        return " / ".join(precipitation)

    sky_types = {"1": "맑음", "3": "구름많음", "4": "흐림"}
    sky = list(
        dict.fromkeys(
            sky_types[value]
            for value in values.get("SKY", [])
            if value in sky_types
        )
    )
    return " / ".join(sky) if sky else "예보 정보 없음"


def _latest_issue_time() -> datetime:
    now = datetime.now(KOREA)
    issue_hour = 18 if now.hour >= 18 else 6 if now.hour >= 6 else 18
    issue_date = now.date() if now.hour >= 6 else now.date() - timedelta(days=1)
    return datetime.combine(issue_date, datetime.min.time(), KOREA).replace(
        hour=issue_hour
    )


def _period_average(
    item: dict, prefix: str, suffixes: tuple[str, ...]
) -> int | None:
    values = [
        int(item[f"{prefix}{suffix}"])
        for suffix in suffixes
        if item.get(f"{prefix}{suffix}") is not None
    ]
    return round(sum(values) / len(values)) if values else None


def _weather_description(
    item: dict, prefix: str, suffixes: tuple[str, ...]
) -> str:
    values = [
        str(item[f"{prefix}{suffix}"])
        for suffix in suffixes
        if item.get(f"{prefix}{suffix}")
    ]
    return " / ".join(dict.fromkeys(values)) if values else "예보 정보 없음"
