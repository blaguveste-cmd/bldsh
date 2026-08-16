import aiohttp

from config import (
    GETSMS_API_KEY,
    GETSMS_API_URL,
    GETSMS_SERVICE_COUNTRY,
    GETSMS_SERVICE_QUERY,
    GETSMS_DEFAULT_OPERATOR,
    GETSMS_MAX_PRICE,
)

HEADERS = {
    "Authorization": f"Bearer {GETSMS_API_KEY}",
    "Content-Type": "application/json",
}


async def _request(method: str, path: str, json=None, params=None):
    url = f"{GETSMS_API_URL.rstrip('/')}{path}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=HEADERS, json=json, params=params) as response:
                data = await response.json()
    except Exception as exc:
        return False, {"error_code": "REQUEST_FAILED", "error_message": str(exc)}

    if not isinstance(data, dict):
        return False, {"error_code": "UNKNOWN_RESPONSE", "error_message": "Response is not JSON object."}

    if not data.get("ok"):
        return False, data

    return True, data.get("data", data)


async def _resolve_country_id(country: str | None):
    if not country:
        return None, None

    if str(country).isdigit():
        return str(country), None

    ok, data = await _request("GET", "/data/countries")
    if not ok:
        return None, data

    query = str(country).lower()
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("id", "")) == query:
            return str(item["id"]), None
        if str(item.get("code", "")).lower() == query:
            return str(item["id"]), None
        if query in str(item.get("name", "")).lower():
            return str(item["id"]), None

    return None, {"error_code": "COUNTRY_NOT_FOUND", "error_message": "Country not found."}


def _match_service(service: dict, query: str) -> bool:
    if not isinstance(service, dict):
        return False
    name = str(service.get("name", "")).lower()
    query = str(query).lower()
    return query in name


async def _service_id_from_country(country_id: str, service_query: str):
    ok, data = await _request("GET", f"/data/services/{country_id}")
    if not ok:
        return None, data

    matches = []
    for service in data.get("items", []):
        if _match_service(service, service_query):
            matches.append(service)

    if not matches:
        return None, None

    exact_matches = [s for s in matches if str(s.get("name", "")).lower() == str(service_query).lower()]
    chosen = min(exact_matches or matches, key=lambda s: float(s.get("price", float("inf"))))
    return chosen.get("id"), None


async def find_service_id(country: str = None, service: str = None):
    country = country or GETSMS_SERVICE_COUNTRY
    service_query = service or GETSMS_SERVICE_QUERY

    resolved_country, _ = await _resolve_country_id(country)
    if resolved_country:
        service_id, error = await _service_id_from_country(resolved_country, service_query)
        if service_id:
            return service_id, None

    ok, data = await _request("GET", "/data/countries")
    if not ok:
        return None, data

    best_service = None
    best_price = float("inf")

    for item in data.get("items", []):
        country_id = str(item.get("id"))
        service_id, error = await _service_id_from_country(country_id, service_query)
        if service_id and error is None:
            ok2, services_data = await _request("GET", f"/data/services/{country_id}")
            if not ok2:
                continue
            for service_item in services_data.get("items", []):
                if str(service_item.get("id")) == str(service_id):
                    try:
                        price = float(service_item.get("price", float("inf")))
                    except (TypeError, ValueError):
                        price = float("inf")
                    if price < best_price:
                        best_price = price
                        best_service = service_id
                    break

    if best_service:
        return best_service, None

    return None, {"error_code": "SERVICE_NOT_FOUND", "error_message": "Service not found in any country."}


async def get_service_price(service_id: int):
    ok, data = await _request("GET", f"/orders/price/{service_id}")
    if not ok:
        return None, data

    if isinstance(data, dict) and data.get("price") is not None:
        return data.get("price"), None

    return None, {"error_code": "PRICE_PARSE_FAILED", "error_message": "Price field is missing."}


async def create_order(service_id: int, operator: str = None, max_price: float = None):
    operator = operator or GETSMS_DEFAULT_OPERATOR
    payload = {
        "service_id": service_id,
        "operator": operator,
        "bot_notifications": False,
    }
    if max_price is not None:
        payload["max_price"] = max_price

    ok, data = await _request("POST", "/orders", json=payload)
    if not ok:
        return None, data

    return data, None


async def get_order(order_id: str):
    ok, data = await _request("GET", f"/orders/{order_id}")
    if not ok:
        return None, data

    return data, None


async def request_another_code(order_id: str):
    ok, data = await _request("POST", f"/orders/{order_id}/request-another-code")
    if not ok:
        return None, data

    return data, None


async def finish_order(order_id: str):
    ok, data = await _request("POST", f"/orders/{order_id}/finish")
    if not ok:
        return None, data

    return data, None
