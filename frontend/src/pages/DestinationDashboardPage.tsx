import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  CloudRain,
  Info,
  Newspaper,
  Shield,
  Star,
} from "lucide-react";

// OLD VERSION: used frontend mock data before backend integration
// import { mockDestinations } from "../data/mockDestinations";

// NEW VERSION: USING BACKEND API DATA
import { getDestinationByCountryCode } from "../services/destinationApi";

import type { Destination } from "../types/country";

function getRiskStyles(riskLevel: Destination["riskLevel"]): string {
  if (riskLevel === "Low") {
    return "border-green-400/40 bg-green-400/10 text-green-400";
  }
  if (riskLevel === "Medium") {
    return "border-yellow-400/40 bg-yellow-400/10 text-yellow-400";
  }
  if (riskLevel === "High") {
    return "border-red-400/40 bg-red-400/10 text-red-400";
  }
  return "border-slate-400/40 bg-slate-400/10 text-slate-400";
}


function getRiskTextClass(riskLevel: Destination["riskLevel"]): string {
  if (riskLevel === "Low") return "text-green-400";
  if (riskLevel === "Medium") return "text-yellow-400";
  if (riskLevel === "High") return "text-red-400";
  return "text-slate-400";
}


// glass banner
function GlassCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`glass-card ${className}`}>
      <div className="glass-card-content">{children}</div>
    </div>
  );
}


// Last Updated
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


function CardIcon({
  icon: Icon,
  className,
  align = "center",
}: {
  icon: React.ElementType;
  className: string;
  align?: "left" | "center";
}) {
  return (
    <div
      className={`mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 ${
        align === "center" ? "mx-auto" : ""
      } ${className}`}
    >
      <Icon size={22} strokeWidth={1.8} />
    </div>
  );
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

  // parallex scrolling
  const [scrollY, setScrollY] = useState<number>(0);

  const newsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    //parallex scroll effect
    function handleScroll() {
      setScrollY(window.scrollY);
    }

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    // if countryCode is missing from the URL, stop fetching
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

  // helper function for scrolling to news section
  function scrollToNews() {
    newsRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(160deg,#030c23_0%,#061428_55%,#02091a_100%)] p-8">
        <GlassCard className="p-8">
          <p className="text-base text-slate-400">
            Loading destination information...
          </p>
        </GlassCard>
      </main>
    );
  }

  if (destination === null) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[linear-gradient(160deg,#030c23_0%,#061428_55%,#02091a_100%)] p-8">
        <GlassCard className="w-full max-w-md p-8">
          <h1 className="text-3xl font-light text-slate-200">
            Destination not found
          </h1>

          <p className="mt-3 text-sm text-slate-400">{errorMessage}</p>

          <Link
            to="/map"
            className="mt-6 inline-block text-sm text-blue-400 hover:text-blue-300"
          >
            ← Back to Map
          </Link>
        </GlassCard>
      </main>
    );
  }

  // Gradually fades and moves the hero section as the user scrolls.
  // Uses screen height so the fade works better on laptops and mobile.
  const fadeStart = window.innerHeight * 1.4;
  const fadeEnd = window.innerHeight * 2.2;
  const heroOpacity = scrollY <= fadeStart ? 1 : Math.max(0, 1 - (scrollY - fadeStart) / (fadeEnd - fadeStart));
  const heroTranslateY = Math.min(scrollY * 0.06, 50);

  return (
    <main className="min-h-screen bg-[linear-gradient(160deg,#030c23_0%,#061428_55%,#02091a_100%)] font-sans">
        <Link to="/map" className="glass-card fixed left-5 top-5 z-50 rounded-full px-4 py-2 text-sm text-slate-400 transition hover:text-slate-200">
          <span className="glass-card-content">← Back to Map</span>
        </Link>

        <section
        className="relative flex min-h-screen flex-col items-center justify-center px-6 py-24"
        style={{
          opacity: heroOpacity,
          transform: `translateY(-${heroTranslateY}px)`,
          pointerEvents: heroOpacity < 0.05 ? "none" : "auto",
        }}
      >
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[40vh] w-[60vw] -translate-x-1/2 -translate-y-[60%] bg-[radial-gradient(ellipse,rgba(59,130,246,0.12)_0%,transparent_70%)]" />

        <p className="mb-4 text-center text-[15px] uppercase tracking-[0.18em] text-slate-400/50">
          Destination Dashboard
        </p>

        <h1 className="mb-5 text-center text-[clamp(100px,15vw,150px)] font-extralight leading-none tracking-[-0.04em] text-slate-100 [text-shadow:0_0_80px_rgba(100,160,255,0.25)]">
          {destination.country}
        </h1>

        <p className="mb-5 text-center text-sm font-light tracking-wide text-slate-400/50">
          {formatLastUpdated(destination.lastUpdated)}
        </p>
        
        <div
          className={`mb-11 rounded-full border px-4 py-1 text-sm tracking-wide backdrop-blur ${getRiskStyles(
            destination.riskLevel
          )}`}
        >
          {destination.riskLevel ?? "Unknown"} Risk
        </div>

        <div className="grid w-full max-w-[820px] gap-3 md:grid-cols-4">
          <GlassCard className="p-6 text-center">
            <CardIcon icon={Star} className="text-amber-300" />

            <p className="mb-3 text-l uppercase tracking-[0.14em] text-slate-400/60">
              Travel Score
            </p>
            <p className="text-6xl font-light leading-relaxed text-slate-200">
              {destination.travelScore !== null
                ? destination.travelScore
                : "—"}
              {destination.travelScore !== null && (
                <span className="text-[30px] font-light text-slate-400/60">
                  /100
                </span>
              )}
            </p>
          </GlassCard>

          <GlassCard className="p-6 text-center">
            <CardIcon icon={Shield} className="text-emerald-300" />
            
            <p className="mb-3 text-l uppercase tracking-[0.14em] text-slate-400/60">
              Risk Level
            </p>
            <p
              className={`${
                destination.riskLevel ? "text-6xl" : "text-4xl"
              } break-words font-light leading-relaxed ${getRiskTextClass(destination.riskLevel)}`}
            >
              {destination.riskLevel ?? "Unknown"}
            </p>
          </GlassCard>

          <GlassCard className="p-6 text-center md:col-span-2">
            <CardIcon icon={AlertTriangle} className="text-orange-300" />

            <p className="mb-3 text-l uppercase tracking-[0.14em] text-slate-400/60">
              Condition
            </p>
            <p
              className={`${
                destination.condition ? "text-6xl" : "text-3xl"
              } break-words font-light leading-relaxed text-slate-300`}
            >
              {destination.condition ?? "No major safety risk available."}
            </p>
          </GlassCard>
        </div>

        <div className="mt-3 grid w-full max-w-[820px] gap-3 md:grid-cols-2">
          <GlassCard className="p-6">
            <CardIcon icon={CloudRain} className="text-blue-300" align = "left" />

            <h2 className="mb-3 text-l uppercase tracking-[0.14em] text-slate-400/60">
              Weather
            </h2>
            <p className="text-3xl font-light leading-relaxed text-slate-300">
              {typeof destination.weather === "string"
                ? destination.weather
                : "Weather information unavailable."}
            </p>
          </GlassCard>

          <GlassCard className="p-6">
            <CardIcon icon={Newspaper} className="text-purple-300" align = "left" />

            <h2 className="mb-3 text-l uppercase tracking-[0.14em] text-slate-400/60">
              Travel Advisory
            </h2>
            <p className="text-3xl font-light leading-relaxed text-slate-300">
              {typeof destination.advisory === "string" &&
              destination.advisory.length > 0
                ? destination.advisory
                : "No advisory information available."}
            </p>
          </GlassCard>
        </div>

        <button
          type="button"
          onClick={scrollToNews}
          className="absolute bottom-7 flex flex-col items-center gap-1 bg-transparent px-4 py-2 text-slate-400/50 transition hover:text-slate-300"
        >
          <span className="text-[11px] uppercase tracking-[0.15em]">
            Show News
          </span>
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-[18px] w-[18px] animate-bounce fill-none stroke-current stroke-2"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
      </section>

      <section ref={newsRef} className="mx-auto max-w-[800px] px-6 py-20">
        <Newspaper size={26} className="text-blue-300" strokeWidth={1.8} />

        <h2 className="mb-7 text-5xl font-light tracking-[0.14em] text-slate-200">
          Top Travel-Related News
        </h2>

        {destination.newsArticles && destination.newsArticles.length > 0 ? (
          <div className="space-y-4">
            {destination.newsArticles.map((article, index) => (
              <article key={article.url} className="glass-card p-7">
                <div className="glass-card-content flex gap-5">
                  <span className="mt-1 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-blue-300/30 bg-white/10 text-base font-light text-blue-200">
                    {article.rankPosition ?? index + 1}
                  </span>

                  <div>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-3xl font-normal leading-snug text-slate-200 transition hover:text-blue-300"
                    >
                      {article.title}
                    </a>

                    <p className="mt-3 text-xl font-light leading-relaxed text-slate-400">
                      {article.abstractedSummary ?? "No summary available."}
                    </p>

                    {article.sourceName && (
                      <p className="mt-3 text-xs tracking-wide text-slate-400/50">
                        {article.sourceName}
                      </p>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <GlassCard className="p-10 text-center">
            <p className="text-xl font-light text-slate-400">
              No travel-related news articles available.
            </p>
          </GlassCard>
        )}

        <GlassCard className="mt-4 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl bg-white/10 text-slate-300">
              <Info size={22} strokeWidth={1.8} />
            </div>

            <div>
              <h2 className="mb-2 text-lg uppercase tracking-[0.14em] text-slate-400/60">
                Upcoming Features
              </h2>

              <p className="text-xl font-light leading-relaxed text-slate-400">
                Flight search, hotel search, and itinerary planning will be added in later milestones.
              </p>
            </div>
          </div>
        </GlassCard>

      </section>
    </main>
  );
}

export default DestinationDashboardPage;