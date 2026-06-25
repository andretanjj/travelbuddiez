export type RiskLevel = "Low" | "Medium" | "High" | "Unknown";

export interface MapDestination {
  countryCode: string;
  country: string;
  city: string;
  mapScore: number | null;
  riskLevel: RiskLevel | null;
  condition: string | null;
  lastUpdated?: string;
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
  newsArticles?: NewsArticle[];
}

export interface NewsArticle {
    title: string;
    abstractedSummary: string | null;
    url: string;
    sourceName: string | null;
    publishedAt: string | null;
    isRelevant?: boolean;
    rankPosition?: number;
}