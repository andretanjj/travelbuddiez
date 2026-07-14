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