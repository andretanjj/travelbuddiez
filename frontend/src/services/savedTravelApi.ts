import { getToken } from "./authApi";

import type {
  SaveFlightRequest,
  SaveHotelRequest,
  SavedFlight,
  SavedHotel,
} from "../types/savedTravel";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function getSavedTravelErrorMessage(response: Response): Promise<string> {
  // FastAPI usually returns errors as { detail: "..." }.
  const errorData = await response.json().catch(() => null);

  return errorData?.detail || "Saved travel request failed";
}

function getAuthHeaders(): HeadersInit {
  /*
    Saved travel endpoints are protected.

    The JWT token is saved in localStorage by authApi.ts during login.
    We send it as Authorization: Bearer <token>.
  */

  const token = getToken();

  if (token === null) {
    throw new Error("Please log in to save travel results.");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function saveFlight(
  flight: SaveFlightRequest
): Promise<SavedFlight> {
  const response = await fetch(`${API_BASE_URL}/saved-travel/flights`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(flight),
  });

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}

export async function saveHotel(hotel: SaveHotelRequest): Promise<SavedHotel> {
  const response = await fetch(`${API_BASE_URL}/saved-travel/hotels`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(hotel),
  });

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}

export async function getSavedFlights(): Promise<{ results: SavedFlight[] }> {
  /*
    Gets all saved flights for the logged-in user.

    Backend route:
    GET /saved-travel/flights

    Requires:
    Authorization: Bearer <token>
  */

  const response = await fetch(`${API_BASE_URL}/saved-travel/flights`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}

export async function getSavedHotels(): Promise<{ results: SavedHotel[] }> {
  /*
    Gets all saved hotels for the logged-in user.

    Backend route:
    GET /saved-travel/hotels

    Requires:
    Authorization: Bearer <token>
  */

  const response = await fetch(`${API_BASE_URL}/saved-travel/hotels`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}

export async function refreshSavedFlight(
  savedFlightId: number
): Promise<SavedFlight> {
  const response = await fetch(
    `${API_BASE_URL}/saved-travel/flights/${savedFlightId}/refresh`,
    {
      method: "PUT",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}

export async function refreshSavedHotel(
  savedHotelId: number
): Promise<SavedHotel> {
  const response = await fetch(
    `${API_BASE_URL}/saved-travel/hotels/${savedHotelId}/refresh`,
    {
      method: "PUT",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}


export async function deleteSavedFlight(
  savedFlightId: number
): Promise<{ message: string; deletedId: number }> {
  /*
    Removes one saved flight from the logged-in user's account.
  */

  const response = await fetch(
    `${API_BASE_URL}/saved-travel/flights/${savedFlightId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}


export async function deleteSavedHotel(
  savedHotelId: number
): Promise<{ message: string; deletedId: number }> {
  /*
    Removes one saved hotel from the logged-in user's account.
  */

  const response = await fetch(
    `${API_BASE_URL}/saved-travel/hotels/${savedHotelId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await getSavedTravelErrorMessage(response));
  }

  return response.json();
}