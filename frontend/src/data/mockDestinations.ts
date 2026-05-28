import type { Destination } from "../types/country.ts";

export const mockDestinations: Destination[] = [
  {
    countryCode: "SGP",
    country: "Singapore",
    travelScore: 88,
    riskLevel: "Low",
    condition: "Safe",
    weather: "Warm and humid, no major weather warnings.",
    news: "No major travel-related disruptions reported.",
  },
  {
    countryCode: "JPN",
    country: "Japan",
    travelScore: 72,
    riskLevel: "Medium",
    condition: "Weather Risk",
    weather: "Possible heavy rain in selected regions.",
    news: "Some areas are monitoring weather-related disruptions.",
  },
  {
    countryCode: "IDN",
    country: "Indonesia",
    travelScore: 48,
    riskLevel: "High",
    condition: "Natural Disaster Risk",
    weather: "Storm and flooding risk in selected regions.",
    news: "Recent reports mention possible regional disruptions.",
  },
];
