import type { Campground, Region, WeatherForecast } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    let detail = `API 요청 실패 (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the HTTP status message when the server response is not JSON.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function getRegions(): Promise<Region[]> {
  return request("/api/regions");
}

export function getCampgrounds(
  region: string,
  campType: string,
): Promise<{ items: Campground[]; total_count: number }> {
  const params = new URLSearchParams({ region });
  if (campType) params.set("type", campType);
  return request(`/api/campgrounds?${params.toString()}`);
}

export function getWeather(
  region: string,
  date: string,
  campground?: Pick<Campground, "map_x" | "map_y">,
): Promise<WeatherForecast> {
  const params = new URLSearchParams({ region, date });
  if (campground?.map_x && campground.map_y) {
    params.set("map_x", campground.map_x);
    params.set("map_y", campground.map_y);
  }
  return request(`/api/weather?${params.toString()}`);
}
