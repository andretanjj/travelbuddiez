import type { Destination } from "../types/country";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getDestinationByCountryCode(
  countryCode: string
): Promise<Destination> {
  console.log("API_BASE_URL:", API_BASE_URL);
  console.log("Fetching:", `${API_BASE_URL}/destinations/${countryCode}`);

  const response = await fetch(`${API_BASE_URL}/destinations/${countryCode}`);

  console.log("Backend response status:", response.status);

  if (!response.ok) {
    throw new Error("Failed to fetch destination");
  }

  return response.json();
}