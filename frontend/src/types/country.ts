// this is the data shape
export type RiskLevel = "Low" | "Medium" | "High";

export type TravelCondition =
    | "Safe"
    | "Weather Risk"
    | "Natural Disaster Risk"
    | "Political Risk"
    | "Social Unrest"
    | "Unknown"

export interface Destination {
  countryCode: string;
  country: string;
  travelScore: number;
  riskLevel: RiskLevel;
  condition: TravelCondition;
  weather: string;
  news: string;
}

