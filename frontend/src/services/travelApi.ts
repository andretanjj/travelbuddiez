import type {
  CurrencyRateResponse,
  FlightSearchResponse,
  HotelSearchResponse,
  TravelPlaceSuggestionResponse,
} from "../types/travel";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function getErrorMessage(response: Response): Promise<string> {
  // Backend usually returns JSON errors.
  // This fallback prevents the frontend from crashing if the response is not JSON.
  const errorData = await response.json().catch(() => null);

  return errorData?.detail || "Travel planning request failed";
}

export async function searchFlights(params: {
  origin: string;
  destination: string;
  departureDate: string;
  returnDate?: string;
  adults: number;
}): Promise<FlightSearchResponse> {
  // URLSearchParams safely builds query strings like:
  // ?origin=SIN&destination=Tokyo&departureDate=2026-07-20&adults=1
  const queryParams = new URLSearchParams({
    origin: params.origin,
    destination: params.destination,
    departureDate: params.departureDate,
    adults: String(params.adults),
  });

  // Only include returnDate for round-trip searches.
  if (params.returnDate) {
    queryParams.set("returnDate", params.returnDate);
  }

  const response = await fetch(
    `${API_BASE_URL}/travel/flights/search?${queryParams.toString()}`
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}

export async function searchHotels(params: {
  city: string;
  checkInDate: string;
  checkOutDate: string;
  adults: number;
}): Promise<HotelSearchResponse> {
  // URLSearchParams keeps the frontend query format consistent with the FastAPI route.
  const queryParams = new URLSearchParams({
    city: params.city,
    checkInDate: params.checkInDate,
    checkOutDate: params.checkOutDate,
    adults: String(params.adults),
  });

  const response = await fetch(
    `${API_BASE_URL}/travel/hotels/search?${queryParams.toString()}`
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}


export async function searchTravelPlaces(
  query: string,
  mode: "flight" | "hotel"
): Promise<TravelPlaceSuggestionResponse> {
  // Backend requires at least 2 characters before searching.
  // mode lets backend rank results differently for flight vs hotel autocomplete.
  const queryParams = new URLSearchParams({
    query,
    mode,
  });

  const response = await fetch(
    `${API_BASE_URL}/travel/places?${queryParams.toString()}`
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}


export async function getCurrencyRate(
  fromCurrency: string,
  toCurrency: string
): Promise<CurrencyRateResponse> {
  const queryParams = new URLSearchParams({
    from: fromCurrency,
    to: toCurrency,
  });

  const response = await fetch(
    `${API_BASE_URL}/travel/currency/rate?${queryParams.toString()}`
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}