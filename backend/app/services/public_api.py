import httpx

TIMEOUT = httpx.Timeout(20.0, connect=10.0)


async def get_public_api_json(
    url: str, params: dict[str, str | int | float]
) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"공공데이터 API HTTP 오류 ({exc.response.status_code})"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError("공공데이터 API 요청에 실패했습니다.") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("공공데이터 API가 JSON이 아닌 응답을 반환했습니다.") from exc

    header = payload.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode") or payload.get("resultCode") or "")
    if result_code and result_code not in {"00", "0000"}:
        message = (
            header.get("resultMsg")
            or payload.get("resultMsg")
            or "알 수 없는 API 오류"
        )
        raise RuntimeError(f"공공데이터 API 오류 ({result_code}): {message}")
    return payload


def get_items(payload: dict) -> list[dict]:
    items = payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []
