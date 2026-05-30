// this is the data shape
export type RiskLevel = "Low" | "Medium" | "High";

export type TravelCondition =
    | "Safe"
    | "Weather Risk"
    | "Natural Disaster Risk"
    | "Political Risk"
    | "Social Unrest"
    | "Unknown"

export interface NewsArticle {
  title: string;
  description?: string;
  url?: string;
  source?: {
    name?: string;
  };
  publishedAt?: string;
}

export interface Destination {
  countryCode: string;
  country: string;
  city: string;
  travelScore: number;
  riskLevel: RiskLevel;
  condition: string;
  weather: string;
  news: NewsArticle[];
  advisory: string;
}

