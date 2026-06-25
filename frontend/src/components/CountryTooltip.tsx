import { motion } from "motion/react";
import { FiAlertTriangle, FiMapPin, FiX } from "react-icons/fi";
import type { MapDestination } from "../types/country.ts";

interface CountryTooltipProps {
  destination: MapDestination;
  x: number;
  y: number;
}

function getRiskBadgeClass(riskLevel: MapDestination["riskLevel"]): string {
  if (riskLevel === "Low") {
    return "border-green-300 bg-green-50 text-green-700";
  }

  if (riskLevel === "Medium") {
    return "border-yellow-300 bg-yellow-50 text-yellow-700";
  }

  return "border-red-300 bg-red-50 text-red-700";
}

function getScoreBarClass(riskLevel: MapDestination["riskLevel"]): string {
  if (riskLevel === "Low") return "bg-green-500";
  if (riskLevel === "Medium") return "bg-yellow-500";
  return "bg-red-500";
}

function CountryTooltip({ destination, x, y }: CountryTooltipProps) {
  const score =
    destination.mapScore !== null && destination.mapScore !== undefined
      ? destination.mapScore
      : 0;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.94, y: 8 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="
                pointer-events-none absolute z-50 w-72 rounded-2xl border border-white/70
                bg-white/95 p-4 text-slate-900 shadow-[0_18px_45px_rgba(15,23,42,0.22)]
                backdrop-blur-md
            "
      style={{
        left: x + 16,
        top: y + 16,
      }}
    >
      <div className="mb-1 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="truncate text-base font-bold text-slate-950">
              {destination.country}
            </h2>

            <span
              className={`
                                inline-flex items-center gap-1 rounded-full border px-2 py-0.5
                                text-[11px] font-semibold
                                ${getRiskBadgeClass(destination.riskLevel)}
                            `}
            >
              <FiAlertTriangle className="h-3 w-3" />
              {destination.riskLevel} Risk
            </span>
          </div>

          <div className="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
            <FiMapPin className="h-3 w-3" />
            <span className="truncate">
              {destination.city || "Destination overview"}
            </span>
          </div>
        </div>

        <FiX className="mt-1 h-3.5 w-3.5 shrink-0 text-slate-300" />
      </div>

      <div className="my-3 h-px bg-slate-200" />

      <div>
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-semibold text-slate-700">
            Safety Score
          </p>

          <p className="text-xs font-bold text-slate-900">
            {destination.mapScore !== null &&
              destination.mapScore !== undefined
              ? `${destination.mapScore}/100`
              : "N/A"}
          </p>
        </div>

        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full ${getScoreBarClass(destination.riskLevel)}`}
            style={{
              width:
                destination.mapScore !== null &&
                  destination.mapScore !== undefined
                  ? `${Math.min(Math.max(score, 0), 100)}%`
                  : "0%",
            }}
          />
        </div>

        <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400">
          <span>Dangerous</span>
          <span>Safe</span>
        </div>
      </div>

      <p className="mt-4 text-xs leading-relaxed text-slate-600">
        {destination.condition}
      </p>

      <p className="mt-3 text-[11px] text-slate-400">
        Updated recently
      </p>
    </motion.div>
  );
}

export default CountryTooltip;