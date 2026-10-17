from xml.etree import ElementTree

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
            detail = _http_error_detail(
                exc.response, str(params.get("serviceKey", ""))
            )
            endpoint = url.rsplit("/", 1)[-1]
            suffix = f": {detail}" if detail else ""
            raise RuntimeError(
                f"공공데이터 API {endpoint} HTTP 오류 "
                f"({exc.response.status_code}){suffix}"
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


def _http_error_detail(response: httpx.Response, service_key: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        service_response = payload.get("OpenAPI_ServiceResponse")
        service_error = (
            service_response.get("cmmMsgHeader")
            if isinstance(service_response, dict)
            else None
        )
        if isinstance(service_error, dict):
            message = service_error.get("returnAuthMsg") or service_error.get(
                "errMsg"
            )
            code = service_error.get("errMsg")
            if message:
                if code and code != message:
                    return f"{message} ({code})"
                return str(message)

        api_response = payload.get("response")
        api_error = (
            api_response.get("header") if isinstance(api_response, dict) else None
        )
        if isinstance(api_error, dict):
            message = api_error.get("resultMsg")
            code = api_error.get("resultCode")
            if message:
                if code:
                    return f"{message} ({code})"
                return str(message)

    try:
        root = ElementTree.fromstring(response.text)
        text = " ".join(part.strip() for part in root.itertext() if part.strip())
    except ElementTree.ParseError:
        text = response.text.strip()

    if service_key:
        text = text.replace(service_key, "[REDACTED]")
    return " ".join(text.split())[:300]


def get_items(payload: dict) -> list[dict]:
    items = payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return items
    return []
