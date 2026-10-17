from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.regions import REGIONS, get_region
from app.services.camping import search_campgrounds
from app.services.weather import get_weather_forecast
from app.settings import settings

app = FastAPI(title="캠핑 날씨 플래너 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/regions")
async def list_regions() -> list[dict[str, str | float | None]]:
    return [region.model_dump() for region in REGIONS.values()]


@app.get("/api/campgrounds")
async def campgrounds(
    region: str,
    radius: int = Query(default=20000, ge=1000, le=200000),
    camp_type: str | None = Query(default=None, alias="type"),
    page: int = Query(default=1, ge=1),
) -> dict:
    try:
        selected_region = get_region(region)
        return await search_campgrounds(
            selected_region, radius=radius, camp_type=camp_type, page=page
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/weather")
async def weather(
    region: str,
    target_date: date = Query(alias="date"),
    map_x: float | None = None,
    map_y: float | None = None,
) -> dict:
    try:
        if (map_x is None) != (map_y is None):
            raise ValueError("캠핑장 좌표 map_x와 map_y를 함께 전달해야 합니다.")
        selected_region = get_region(region)
        return await get_weather_forecast(
            selected_region, target_date, map_x=map_x, map_y=map_y
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
