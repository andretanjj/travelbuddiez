export interface Destination {
  countryCode: string;
  country: string;
  city: string;
  travelScore: number;
  mapScore?: number;
  riskLevel: "Low" | "Medium" | "High";
  condition: string;
  weather: string;
  news: string;
  advisory: string;
}