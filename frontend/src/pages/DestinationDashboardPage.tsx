import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  CloudRain,
  Info,
  Newspaper,
  Shield,
  Star,
} from "lucide-react";

import { getDestinationByCountryCode } from "../services/destinationApi";
import type { Destination } from "../types/country";

function getRiskBadgeClass(riskLevel: Destination["riskLevel"]): string {
  if (riskLevel === "Low") {
    return "bg-green-100 text-green-700 border-green-200";
  }

  if (riskLevel === "Medium") {
    return "bg-yellow-100 text-yellow-700 border-yellow-200";
  }

  if (riskLevel === "High") {
    return "bg-red-100 text-red-700 border-red-200";
  }

  return "bg-gray-100 text-gray-700 border-gray-200";
}

function getRiskDotClass(riskLevel: Destination["riskLevel"]): string {
  if (riskLevel === "Low") return "bg-green-500";
  if (riskLevel === "Medium") return "bg-yellow-500";
  if (riskLevel === "High") return "bg-red-500";
  return "bg-gray-500";
}

function splitNewsItems(news: Destination["news"]): string[] {
  if (typeof news !== "string" || news.trim().length === 0) {
    return [];
  }

  return news
    .split("|")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function StatCard({
  label,
  value,
  icon: Icon,
  iconBg,
  iconColor,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <div
        className={`flex h-9 w-9 items-center justify-center rounded-xl ${iconBg}`}
      >
        <Icon size={16} className={iconColor} />
      </div>

      <div>
        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-gray-500">
          {label}
        </p>

        <p className="text-xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

function formatLastUpdated(lastUpdated: string | null | undefined): string {
  if (!lastUpdated) {
    return "Last updated: Not available";
  }

  const date = new Date(lastUpdated);

  if (Number.isNaN(date.getTime())) {
    return "Last updated: Not available";
  }

  return `Last updated: ${date.toLocaleString("en-SG", {
    timeZone: "Asia/Singapore",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  })}`;
}

function DestinationDashboardPage() {
  const { countryCode } = useParams();

  const [destination, setDestination] = useState<Destination | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    if (countryCode === undefined) {
      setIsLoading(false);
      setErrorMessage("Country code is missing.");
      return;
    }

    async function fetchDestination(countryCode: string) {
      try {
        setIsLoading(true);
        setErrorMessage("");

        const data = await getDestinationByCountryCode(countryCode);

        setDestination(data);
      } catch {
        setDestination(null);
        setErrorMessage("Unable to load destination information.");
      } finally {
        setIsLoading(false);
      }
    }

    fetchDestination(countryCode);
  }, [countryCode]);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-700">
            Loading destination information...
          </p>
        </div>
      </main>
    );
  }

  if (destination === null) {
    return (
      <main className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h1 className="mb-3 text-2xl font-bold text-gray-900">
            Destination not found
          </h1>

          <p className="mb-6 text-sm text-gray-600">{errorMessage}</p>

          <Link
            to="/map"
            className="inline-flex rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700"
          >
            Back to Map
          </Link>
        </div>
      </main>
    );
  }

  const newsItems = splitNewsItems(destination.news);

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto flex max-w-4xl flex-col gap-7">
        <Link
          to="/map"
          className="w-fit text-sm font-medium text-blue-600 transition hover:text-blue-700"
        >
          ← Back to Map
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="mb-1 text-xs font-medium text-gray-500">
              Destination Dashboard
            </p>

            <h1 className="text-4xl font-bold tracking-tight text-gray-900">
              {destination.country}
            </h1>
            
            <p className="mt-2 text-xs text-gray-500">
              {formatLastUpdated(destination.lastUpdated)}
            </p>
          </div>

          <span
            className={`mt-1 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold ${getRiskBadgeClass(
              destination.riskLevel
            )}`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${getRiskDotClass(
                destination.riskLevel
              )}`}
            />

            {destination.riskLevel ?? "Unknown"} Risk
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            label="Travel Score"
            value={
              destination.travelScore !== null
                ? `${destination.travelScore}/100`
                : "N/A"
            }
            icon={Star}
            iconBg="bg-amber-50"
            iconColor="text-amber-500"
          />

          <StatCard
            label="Risk Level"
            value={destination.riskLevel ?? "Unknown"}
            icon={Shield}
            iconBg="bg-green-50"
            iconColor="text-green-600"
          />

          <StatCard
            label="Condition"
            value={destination.condition ?? "Unavailable"}
            icon={AlertTriangle}
            iconBg="bg-orange-50"
            iconColor="text-orange-500"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50">
                <CloudRain size={16} className="text-blue-500" />
              </div>

              <h2 className="text-sm font-semibold text-gray-900">Weather</h2>
            </div>

            <p className="text-sm leading-relaxed text-gray-700">
              {typeof destination.weather === "string" &&
                destination.weather.length > 0
                ? destination.weather
                : "Weather information unavailable."}
            </p>
          </div>

          <div className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-50">
                <Newspaper size={16} className="text-purple-500" />
              </div>

              <h2 className="text-sm font-semibold text-gray-900">
                Travel Advisory
              </h2>
            </div>

            <p className="text-sm leading-relaxed text-gray-700">
              {typeof destination.advisory === "string" &&
                destination.advisory.length > 0
                ? destination.advisory
                : "No advisory information available."}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-900">
            Latest Travel-Related News
          </h2>

          {newsItems.length > 0 ? (
            <ul className="flex flex-col divide-y divide-gray-200">
              {newsItems.map((item, index) => (
                <li
                  key={`${item}-${index}`}
                  className="flex items-start gap-3 py-3 first:pt-0 last:pb-0"
                >
                  <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-500">
                    {index + 1}
                  </span>

                  <p className="text-sm leading-relaxed text-gray-700">
                    {item}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-700">
              No major travel-related news found.
            </p>
          )}
        </div>

        <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gray-100">
            <Info size={16} className="text-gray-500" />
          </div>

          <div>
            <h2 className="mb-1 text-sm font-semibold text-gray-900">
              Upcoming Features
            </h2>

            <p className="text-sm leading-relaxed text-gray-500">
              Flight search, hotel search, and itinerary planning will be added
              in later milestones.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

export default DestinationDashboardPage;