// Types for the Travel Planning page.
// These match the simplified JSON returned by the backend /travel routes.

export type ActiveTravelTab = "flights" | "hotels";

export interface FlightResult {
  id: string;
  city: string;
  country: string;
  route: string;
  price: number;
  currency: string;
  airline: string;
  duration: string;
  stops: string;
  departureDate: string;
}

export interface HotelResult {
  id: string;
  name: string;
  city: string;
  country: string;
  price: number;
  currency: string;
  rating: number;
  checkInDate: string;
  checkOutDate: string;
}

export interface FlightSearchResponse {
  results: FlightResult[];
}

export interface HotelSearchResponse {
  results: HotelResult[];
}

// Suggestion shown in the Travel Planning autocomplete dropdown.
// Backend returns this from GET /travel/places?query=...
export interface TravelPlaceSuggestion {
  id: string;
  name: string;
  subtitle: string | null;
  code: string | null;
  city: string | null;
  country: string | null;
  countryCode: string | null;
  type: string;
  provider: string;
}

export interface TravelPlaceSuggestionResponse {
  results: TravelPlaceSuggestion[];
}