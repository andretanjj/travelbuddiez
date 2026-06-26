export type Flight = {
  id: number;
  city: string;
  country: string;
  route: string;
  price: number;
  airline: string;
  duration: string;
  stops: string;
};

export type Hotel = {
  id: number;
  name: string;
  city: string;
  country: string;
  price: number;
  rating: number;
};

export const mockFlights: Flight[] = [
  {
    id: 1,
    city: "Tokyo",
    country: "Japan",
    route: "SIN → NRT",
    price: 420,
    airline: "Scoot",
    duration: "6h 50m",
    stops: "Direct",
  },
  {
    id: 2,
    city: "Bali",
    country: "Indonesia",
    route: "SIN → DPS",
    price: 180,
    airline: "AirAsia",
    duration: "2h 45m",
    stops: "Direct",
  },
  {
    id: 3,
    city: "Bangkok",
    country: "Thailand",
    route: "SIN → BKK",
    price: 150,
    airline: "Thai Airways",
    duration: "2h 30m",
    stops: "Direct",
  },
  {
    id: 4,
    city: "Seoul",
    country: "South Korea",
    route: "SIN → ICN",
    price: 390,
    airline: "Korean Air",
    duration: "6h 20m",
    stops: "Direct",
  },
  {
    id: 5,
    city: "Kuala Lumpur",
    country: "Malaysia",
    route: "SIN → KUL",
    price: 95,
    airline: "Jetstar Asia",
    duration: "1h 10m",
    stops: "Direct",
  },
  {
    id: 6,
    city: "Taipei",
    country: "Taiwan",
    route: "SIN → TPE",
    price: 310,
    airline: "China Airlines",
    duration: "4h 45m",
    stops: "Direct",
  },
];

export const mockHotels: Hotel[] = [
  {
    id: 1,
    name: "Tokyo Bay Hotel",
    city: "Tokyo",
    country: "Japan",
    price: 180,
    rating: 9.1,
  },
  {
    id: 2,
    name: "Bali Garden Resort",
    city: "Bali",
    country: "Indonesia",
    price: 95,
    rating: 8.8,
  },
  {
    id: 3,
    name: "Bangkok City Hotel",
    city: "Bangkok",
    country: "Thailand",
    price: 70,
    rating: 8.5,
  },
  {
    id: 4,
    name: "Seoul Central Stay",
    city: "Seoul",
    country: "South Korea",
    price: 160,
    rating: 9.0,
  },
  {
    id: 5,
    name: "KL Downtown Hotel",
    city: "Kuala Lumpur",
    country: "Malaysia",
    price: 65,
    rating: 8.4,
  },
  {
    id: 6,
    name: "Taipei Modern Inn",
    city: "Taipei",
    country: "Taiwan",
    price: 120,
    rating: 8.7,
  },
];