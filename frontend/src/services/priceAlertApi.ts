import { getToken } from "./authApi";

import type {
  PriceAlert,
  PriceAlertResponse,
} from "../types/priceAlert";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function getAuthHeaders(): HeadersInit {
  /*
    Price-alert endpoints require the logged-in user's JWT.
  */

  const token = getToken();

  if (token === null) {
    throw new Error("Please log in to create a price alert.");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function getErrorMessage(response: Response): Promise<string> {
  /*
    FastAPI usually returns errors using:
    { "detail": "Error message" }
  */

  const errorData = await response.json().catch(() => null);

  return errorData?.detail || "Price alert request failed.";
}

export async function createFlightPriceAlert(
  savedFlightId: number,
  targetPrice: number,
  targetCurrency: string
): Promise<PriceAlert> {
  const response = await fetch(
    `${API_BASE_URL}/price-alerts/flights/${savedFlightId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        target_price: targetPrice,
        target_currency: targetCurrency,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}

export async function createHotelPriceAlert(
  savedHotelId: number,
  targetPrice: number,
  targetCurrency: string
): Promise<PriceAlert> {
  const response = await fetch(
    `${API_BASE_URL}/price-alerts/hotels/${savedHotelId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        target_price: targetPrice,
        target_currency: targetCurrency,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}

export async function getPriceAlerts(): Promise<PriceAlertResponse> {
  const response = await fetch(`${API_BASE_URL}/price-alerts`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}

export async function deactivatePriceAlert(
  alertId: number
): Promise<PriceAlert> {
  const response = await fetch(
    `${API_BASE_URL}/price-alerts/${alertId}/deactivate`,
    {
      method: "PUT",
      headers: getAuthHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}