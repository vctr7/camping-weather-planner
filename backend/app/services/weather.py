from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.regions import Region
from app.services.public_api import get_items, get_public_api_json
from app.settings import settings

LAND_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"
TEMPERATURE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
KOREA = ZoneInfo("Asia/Seoul")


async def get_weather_forecast(region: Region, target_date: date) -> dict:
    if not settings.weather_api_service_key:
        raise RuntimeError("WEATHER_API_SERVICE_KEY 환경변수를 설정해야 합니다.")

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
    }


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
