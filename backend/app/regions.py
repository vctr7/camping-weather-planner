from pydantic import BaseModel


class Region(BaseModel):
    id: str
    name: str
    map_x: float
    map_y: float
    land_reg_id: str
    temperature_reg_id: str


REGIONS = {
    region.id: region
    for region in [
        Region(
            id="seoul",
            name="서울",
            map_x=126.9780,
            map_y=37.5665,
            land_reg_id="11B00000",
            temperature_reg_id="11B10101",
        ),
        Region(
            id="gyeonggi",
            name="경기",
            map_x=127.0286,
            map_y=37.2636,
            land_reg_id="11B00000",
            temperature_reg_id="11B20601",
        ),
        Region(
            id="gangneung",
            name="강원 강릉",
            map_x=128.8761,
            map_y=37.7519,
            land_reg_id="11D20000",
            temperature_reg_id="11D20501",
        ),
        Region(
            id="daejeon",
            name="대전",
            map_x=127.3845,
            map_y=36.3504,
            land_reg_id="11C20000",
            temperature_reg_id="11C20401",
        ),
        Region(
            id="gwangju",
            name="광주",
            map_x=126.8526,
            map_y=35.1595,
            land_reg_id="11F20000",
            temperature_reg_id="11F20501",
        ),
        Region(
            id="daegu",
            name="대구",
            map_x=128.6014,
            map_y=35.8714,
            land_reg_id="11H10000",
            temperature_reg_id="11H10701",
        ),
        Region(
            id="busan",
            name="부산",
            map_x=129.0756,
            map_y=35.1796,
            land_reg_id="11H20000",
            temperature_reg_id="11H20201",
        ),
        Region(
            id="jeju",
            name="제주",
            map_x=126.5312,
            map_y=33.4996,
            land_reg_id="11G00000",
            temperature_reg_id="11G00201",
        ),
    ]
}


def get_region(region_id: str) -> Region:
    try:
        return REGIONS[region_id]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 지역입니다: {region_id}") from exc
