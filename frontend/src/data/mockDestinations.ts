export type RiskLevel = "Low" | "Medium" | "High";

export interface MockDestination {
  countryCode: string; // ISO A3 code for later backend integration
  country: string;
  travelScore: number;
  riskLevel: RiskLevel;
}

export const mockDestinations: MockDestination[] = [
  {
    countryCode: "SGP",
    country: "Singapore",
    travelScore: 85,
    riskLevel: "Low",
  },
  {
    countryCode: "JPN",
    country: "Japan",
    travelScore: 70,
    riskLevel: "Medium",
  },
  {
    countryCode: "IDN",
    country: "Indonesia",
    travelScore: 45,
    riskLevel: "High",
  },
];