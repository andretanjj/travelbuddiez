// Types for the Travel Planning page.
// These match the simplified JSON returned by the backend /travel routes.

export type ActiveTravelTab = "flights" | "hotels";

export interface FlightResult {
  id: string;
  providerItemId: string;

  city: string;
  country: string;

  // Outbound journey.
  route: string;
  departureDate: string;
  departureAt: string | null;
  duration: string;
  stops: string;

  // Return journey.
  // These stay null for one-way searches.
  returnRoute: string | null;
  returnDate: string | null;
  returnDepartureAt: string | null;
  returnDuration: string | null;
  returnStops: string | null;
  returnFlightNumber: string | null;

  // Price is Duffel's total offer price.
  price: number;
  currency: string;

  airline: string;
  flightNumber: string | null;
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