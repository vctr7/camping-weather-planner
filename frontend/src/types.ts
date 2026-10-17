export interface Region {
  id: string;
  name: string;
  map_x: number;
  map_y: number;
  land_reg_id: string;
  temperature_reg_id: string;
}

export interface Campground {
  content_id: string;
  name: string;
  address: string;
  province: string;
  district: string;
  type: string;
  facilities: string[];
  pet_allowed: string;
  reservation_url: string;
  image_url: string;
  map_x: string | null;
  map_y: string | null;
  tel: string;
  description: string;
}

export interface WeatherForecast {
  region: Region;
  date: string;
  forecast_day: number;
  issued_at: string;
  precipitation_probability: number | null;
  weather: string;
  min_temperature: number | null;
  max_temperature: number | null;
}

export interface SavedPlan {
  id?: string;
  campground: Campground;
  region: string;
  date: string;
  created_at?: string;
}
