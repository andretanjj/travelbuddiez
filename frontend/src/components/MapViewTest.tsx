import { useRef, useEffect, useState } from "react";
import { AnimatePresence } from "motion/react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import CountryTooltip from "./CountryTooltip.tsx";
import type { Destination } from "../types/country";

interface TooltipState {
  destination: Destination;
  x: number;
  y: number;
}

// convert travel score into map colour
function getColor(score: number): string {
  if (score >= 75) return "#9DE08B";
  if (score >= 50) return "#FFFE52";
  return "#F50000";
}

function MapViewTest() {
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const hoveredCountryIdRef = useRef<string | null>(null);

  // 1. Fetch backend data
  useEffect(() => {
    fetch("http://127.0.0.1:8000/destinations")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Backend error: ${res.status}`);
        }
        return res.json();
      })
      .then((data: Destination[]) => {
        console.log("Backend destinations:", data);
        setDestinations(data);
      })
      .catch((err) => {
        console.error("Failed to fetch destinations:", err);
      });
  }, []);

  // 2. Create map only once
  useEffect(() => {
    if (mapContainerRef.current === null) return;
    if (mapRef.current !== null) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

    console.log("Mapbox token:", import.meta.env.VITE_MAPBOX_TOKEN);

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/standard",
      config: {
        basemap: { theme: "monochrome" },
      },
      center: [103.8198, 1.3521],
      zoom: 3,
    });

    mapRef.current = map;

    map.on("load", () => {
      map.addSource("countries", {
        type: "geojson",
        data: "/countries.geojson",
        promoteId: "ISO3166-1-Alpha-3",
      });

      map.addLayer({
        id: "country-fill",
        type: "fill",
        source: "countries",
        paint: {
          // Start transparent first. Backend data will update this later.
          "fill-color": "transparent",

          "fill-opacity": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            0.75,
            0.5,
          ],
        },
      });

      map.addLayer({
        id: "country-outline",
        type: "line",
        source: "countries",
        paint: {
          "line-color": "#111827",
          "line-width": [
            "case",
            ["boolean", ["feature-state", "hover"], false],
            1.5,
            0.5,
          ],
        },
      });

      function clearHoveredCountry(): void {
        if (hoveredCountryIdRef.current !== null) {
          map.setFeatureState(
            {
              source: "countries",
              id: hoveredCountryIdRef.current,
            },
            {
              hover: false,
            }
          );
        }

        hoveredCountryIdRef.current = null;
      }

      map.on("mousemove", "country-fill", (event) => {
        const feature = event.features?.[0];
        if (feature === undefined) return;

        const countryCode = feature.properties?.["ISO3166-1-Alpha-3"];
        if (typeof countryCode !== "string") return;

        clearHoveredCountry();

        hoveredCountryIdRef.current = countryCode;

        map.setFeatureState(
          {
            source: "countries",
            id: countryCode,
          },
          {
            hover: true,
          }
        );

        const destination = destinations.find(
          (destination) => destination.countryCode === countryCode
        );

        if (destination === undefined) {
          map.getCanvas().style.cursor = "";
          setTooltip(null);
          return;
        }

        map.getCanvas().style.cursor = "pointer";

        setTooltip({
          destination,
          x: event.point.x,
          y: event.point.y,
        });
      });

      map.on("mouseleave", "country-fill", () => {
        clearHoveredCountry();
        map.getCanvas().style.cursor = "";
        setTooltip(null);
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 3. Update country colours whenever backend data arrives
  useEffect(() => {
    if (!mapRef.current) return;
    if (destinations.length === 0) return;

    const map = mapRef.current;

    function updateCountryColours() {
      if (!map.getLayer("country-fill")) {
        console.log("country-fill layer not ready yet");
        return;
      }

      const colourExpression: any[] = [
        "match",
        ["get", "ISO3166-1-Alpha-3"],
        ...destinations.flatMap((destination) => [
          destination.countryCode,
          getColor(destination.travelScore),
        ]),
        "transparent",
      ];

      console.log("Updating map colours:", colourExpression);

      map.setPaintProperty(
        "country-fill",
        "fill-color",
        colourExpression as unknown as mapboxgl.Expression
      );
    }

    if (map.loaded() && map.getLayer("country-fill")) {
      updateCountryColours();
    } else {
      map.once("load", updateCountryColours);
    }
  }, [destinations]);

  return (
    <div className="relative h-[calc(100vh-60px)] w-full">
      <div className="h-full w-full" ref={mapContainerRef} />

      <AnimatePresence>
        {tooltip !== null && (
          <CountryTooltip
            destination={tooltip.destination}
            x={tooltip.x}
            y={tooltip.y}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default MapViewTest;