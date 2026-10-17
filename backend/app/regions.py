from pydantic import BaseModel


class Region(BaseModel):
    id: str
    name: str
    map_x: float
    map_y: float
    land_reg_id: str
    temperature_reg_id: str
    area_code: str | None = None


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
            area_code="1",
        ),
        Region(
            id="incheon",
            name="인천",
            map_x=126.7052,
            map_y=37.4563,
            land_reg_id="11B00000",
            temperature_reg_id="11B20201",
            area_code="2",
        ),
        Region(
            id="daejeon",
            name="대전",
            map_x=127.3845,
            map_y=36.3504,
            land_reg_id="11C20000",
            temperature_reg_id="11C20401",
            area_code="3",
        ),
        Region(
            id="daegu",
            name="대구",
            map_x=128.6014,
            map_y=35.8714,
            land_reg_id="11H10000",
            temperature_reg_id="11H10701",
            area_code="4",
        ),
        Region(
            id="gwangju",
            name="광주",
            map_x=126.8526,
            map_y=35.1595,
            land_reg_id="11F20000",
            temperature_reg_id="11F20501",
            area_code="5",
        ),
        Region(
            id="busan",
            name="부산",
            map_x=129.0756,
            map_y=35.1796,
            land_reg_id="11H20000",
            temperature_reg_id="11H20201",
            area_code="6",
        ),
        Region(
            id="ulsan",
            name="울산",
            map_x=129.3114,
            map_y=35.5384,
            land_reg_id="11H20000",
            temperature_reg_id="11H20101",
            area_code="7",
        ),
        Region(
            id="sejong",
            name="세종",
            map_x=127.2890,
            map_y=36.4800,
            land_reg_id="11C20000",
            temperature_reg_id="11C20401",
            area_code="8",
        ),
        Region(
            id="gyeonggi",
            name="경기",
            map_x=127.0286,
            map_y=37.2636,
            land_reg_id="11B00000",
            temperature_reg_id="11B20601",
            area_code="31",
        ),
        Region(
            id="gangneung",
            name="강원도",
            map_x=128.8761,
            map_y=37.7519,
            land_reg_id="11D20000",
            temperature_reg_id="11D20501",
            area_code="32",
        ),
        Region(
            id="chungbuk",
            name="충북",
            map_x=127.4890,
            map_y=36.6424,
            land_reg_id="11C10000",
            temperature_reg_id="11C10301",
            area_code="33",
        ),
        Region(
            id="chungnam",
            name="충남",
            map_x=126.8000,
            map_y=36.5184,
            land_reg_id="11C20000",
            temperature_reg_id="11C20401",
            area_code="34",
        ),
        Region(
            id="gyeongbuk",
            name="경북",
            map_x=128.7298,
            map_y=36.5684,
            land_reg_id="11H10000",
            temperature_reg_id="11H10701",
            area_code="35",
        ),
        Region(
            id="gyeongnam",
            name="경남",
            map_x=128.6811,
            map_y=35.2281,
            land_reg_id="11H20000",
            temperature_reg_id="11H20201",
            area_code="36",
        ),
        Region(
            id="jeonbuk",
            name="전북",
            map_x=127.1480,
            map_y=35.8242,
            land_reg_id="11F10000",
            temperature_reg_id="11F10201",
            area_code="37",
        ),
        Region(
            id="jeonnam",
            name="전남",
            map_x=126.4629,
            map_y=34.8161,
            land_reg_id="11F20000",
            temperature_reg_id="11F20501",
            area_code="38",
        ),
        Region(
            id="jeju",
            name="제주",
            map_x=126.5312,
            map_y=33.4996,
            land_reg_id="11G00000",
            temperature_reg_id="11G00201",
            area_code="39",
        ),
    ]
}


def get_region(region_id: str) -> Region:
    try:
        return REGIONS[region_id]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 지역입니다: {region_id}") from exc
