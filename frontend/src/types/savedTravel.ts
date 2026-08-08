export type PriceStatus =
  | "saved_only"
  | "price_dropped"
  | "price_increased"
  | "unchanged"
  | "unavailable";

export interface SaveFlightRequest {
  provider_item_id: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  departure_date: string;
  return_date?: string | null;
  price: number;
  currency: string;
  airline: string;
  flight_number: string | null;
  departure_at: string | null;
  return_flight_number: string | null;
  return_departure_at: string | null;
  duration: string;
  stops: string;
  provider: string;
}

export interface SaveHotelRequest {
  provider_item_id: string;
  destination_code: string;
  destination_name: string;
  hotel_name: string;
  city: string;
  country: string;
  rating: number;
  price: number;
  currency: string;
  check_in_date: string;
  check_out_date: string;
  provider: string;
}

export interface SavedFlight extends SaveFlightRequest {
  id: number;
  user_id: number;
  saved_price: number;
  current_price: number | null;
  saved_at: string;
  last_checked_at: string | null;
  price_status: PriceStatus;
}

export interface SavedHotel extends SaveHotelRequest {
  id: number;
  user_id: number;
  saved_price: number;
  current_price: number | null;
  saved_at: string;
  last_checked_at: string | null;
  price_status: PriceStatus;
}