import { motion } from "motion/react";
import type { Destination } from "../types/country.ts";

// properties to pass data from parent component to child component
interface CountryTooltipProps {
    // destination obj contains all travel-related info to display
    destination:  Destination;
    
    // mouse pos inside map container
    x: number;
    y: number;
}

// returns different Tailwind classers depending on riskLevel
function getRiskBadgeClass(riskLevel: Destination["riskLevel"]): string {
    if (riskLevel === "Low") return "bg-green-100 text-green-700";
    else if (riskLevel === "Medium") return "bg-yellow-100 text-yellow-700";
    return "bg-red-100 text-red-700";

}

function CountryTooltip({ destination, x, y}: CountryTooltipProps) {
    return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 8 }} // initial animation state before tooltip appears
      animate={{ opacity: 1, scale: 1, y: 0 }}   // animation state when tooltip is visible
      exit={{ opacity: 0, scale: 0.9, y: 8 }}    // animation state when tooltip disappears
      transition={{ duration: 0.18, ease: "easeOut" }} // speed of popup
      className="pointer-events-none absolute z-50 w-64 rounded-2xl border border-white/30 bg-white/95 p-4 shadow-xl backdrop-blur-md"
      // places tooltip near the cursor, with small offset so it does not cover the pointer
      style={{
        left: x + 16,
        top: y + 16,
      }}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-gray-900">
          {destination.country}
        </h2>

        <span
          className={`rounded-full px-2 py-1 text-xs font-semibold ${getRiskBadgeClass(destination.riskLevel)}`}
        >
          {destination.riskLevel} Risk
        </span>
      </div>

      <div className="space-y-1 text-sm text-gray-700">
        <p>
          <span className="font-medium text-gray-900">Travel Score:</span>{" "}
          {destination.travelScore}/100
        </p>

        <p>
          <span className="font-medium text-gray-900">Condition:</span>{" "}
          {destination.condition}
        </p>
      </div>
    </motion.div>
  );

}

export default CountryTooltip;