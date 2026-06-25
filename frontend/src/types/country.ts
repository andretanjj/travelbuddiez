export type RiskLevel = "Low" | "Medium" | "High" | "Unknown";

export interface MapDestination {
  countryCode: string;
  country: string;
  city: string;
  mapScore: number | null;
  riskLevel: RiskLevel | null;
  condition: string | null;
  lastUpdated?: string | null;
}

export interface Destination {
  countryCode: string;
  country: string;
  city: string;
  travelScore: number | null;
  riskLevel: RiskLevel | null;
  condition: string | null;
  weather: string | null;
  news: string | null;
  advisory: string | null;
  lastUpdated?: string;
}