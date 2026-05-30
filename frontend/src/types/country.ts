// this is the data shape
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

  // Used by MapView and CountryTooltip.
  mapScore?: number | null;

  // Used by DestinationDashboardPage.
  travelScore?: number;

  riskLevel: "Low" | "Medium" | "High" | "Unknown";
  condition: string;

  weather?: unknown;
  news?: NewsArticle[];
  advisory?: unknown;
}
