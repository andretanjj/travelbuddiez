import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

// OLD VERSION: used frontend mock data before backend integration
// import { mockDestinations } from "../data/mockDestinations";

import type { Destination } from "../types/country";

function getRiskBadgeClass(riskLevel: Destination["riskLevel"]): string {
  if (riskLevel === "Low") return "bg-green-100 text-green-700";
  else if (riskLevel === "Medium") return "bg-yellow-100 text-yellow-700";
  return "bg-red-100 text-red-700";
}

function DestinationDashboardPage() {
  // reads countryCode from URL, e.g. /destinations/SGP
  const { countryCode } = useParams();

  // OLD VERSION: find destination directly from frontend mockDestinations
  // const destination = mockDestinations.find(
  //   (destination) => destination.countryCode === countryCode
  // );

  // NEW VERSION: destination data will come from backend API
  const [destination, setDestination] = useState<Destination | null>(null);

  // tracks whether data is still being fetched
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // stores error message if backend request fails
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    // if countryCode is missing from the URL, stop fetching
    if (countryCode === undefined) {
      setIsLoading(false);
      setErrorMessage("Country code is missing.");
      return;
    }

    // backend base URL from frontend .env file
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

    async function fetchDestination() {
      try {
        setIsLoading(true);
        setErrorMessage("");

        // fetch destination data from FastAPI backend
        const response = await fetch(
          `${apiBaseUrl}/destinations/${countryCode}`
        );

        // if backend returns 404 or another error, show error state
        if (!response.ok) {
          throw new Error("Destination not found");
        }

        // convert backend JSON response into Destination type
        const data: Destination = await response.json();

        setDestination(data);
      } catch {
        setDestination(null);
        setErrorMessage("Unable to load destination information.");
      } finally {
        setIsLoading(false);
      }
    }

    fetchDestination();
  }, [countryCode]);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-3xl rounded-2xl bg-white p-6 shadow">
          <p className="text-gray-700">Loading destination information...</p>
        </div>
      </main>
    );
  }

  if (destination === null) {
    return (
      <main className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-3xl rounded-2xl bg-white p-6 shadow">
          <h1 className="mb-3 text-2xl font-bold text-gray-900">
            Destination not found
          </h1>

          <p className="mb-6 text-gray-600">
            {errorMessage}
          </p>

          <Link
            to="/map"
            className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white"
          >
            Back to Map
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-4xl">
        <Link to="/map" className="text-sm font-medium text-blue-600">
          ← Back to Map
        </Link>

        <section className="mt-6 rounded-2xl bg-white p-6 shadow">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">
                Destination Dashboard
              </p>

              <h1 className="mt-1 text-3xl font-bold text-gray-900">
                {destination.country}
              </h1>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-sm font-semibold ${getRiskBadgeClass(
                destination.riskLevel
              )}`}
            >
              {destination.riskLevel} Risk
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Travel Score</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {destination.travelScore}/100
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Risk Level</p>
              <p className="mt-2 text-xl font-semibold text-gray-900">
                {destination.riskLevel}
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Condition</p>
              <p className="mt-2 text-xl font-semibold text-gray-900">
                {destination.condition}
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-gray-200 p-4">
              <h2 className="mb-2 text-lg font-semibold text-gray-900">
                Weather
              </h2>
              <p className="text-gray-700">{destination.weather}</p>
            </div>

            <div className="rounded-xl border border-gray-200 p-4">
              <h2 className="mb-2 text-lg font-semibold text-gray-900">
                News
              </h2>
              <p className="text-gray-700">{destination.news}</p>
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-dashed border-gray-300 p-4">
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              Upcoming Features
            </h2>

            <p className="text-gray-700">
              Flight search, hotel search, and itinerary planning will be added
              in later milestones.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

export default DestinationDashboardPage;