import type { Destination } from "../types/country";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getDestinationByCountryCode(
  countryCode: string
): Promise<Destination> {
  const response = await fetch(`${API_BASE_URL}/destinations/${countryCode}`);

  if (!response.ok) {
    throw new Error("Failed to fetch destination");
  }

  return response.json();
}