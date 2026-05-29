import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import { mockDestinations } from "../data/mockDestinations";
import CountryTooltip from "./CountryTooltip.tsx";
import type { Destination } from "../types/country";

// stores data needed to display the tooltip (same as CountryTooltip)
interface TooltipState {
    destination: Destination;
    x: number;
    y: number;
}

// finds matching mock destination based on country code from GeoJSON
function findDestinationByCountryCode(countryCode: string): Destination | undefined {
    return mockDestinations.find(
        (destination: Destination) => destination.countryCode === countryCode
    );
}

// convert travel score into map color
function getColor(score: number): string {
    if (score >= 75) return "#29bd29";
    else if (score >= 50) return "#ffff00";
    return "#f32e2e";
}

function MapView() {
  // mapbox map object
  const mapRef = useRef<mapboxgl.Map | null>(null) 

  // stores html div that mapbox will render map into
  const mapContainerRef = useRef<HTMLDivElement | null>(null) 

  // tracks curr hovered country ID for Mapbox feature-state hover styling
  const hoveredCountryIdRef = useRef<string | null>(null);

  // React state for tooltip currently shown on hover
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  // allows this component to move to another page (DestinationDashboardPage)
  const navigate = useNavigate();

  useEffect(() => {

    if (mapContainerRef.current === null) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

    // mapbox map instance
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/standard',
      config: {
        basemap: { theme: "monochrome"},
      },
      center: [103.8198, 1.3521], // shows SG by default
      zoom: 10,
    });

    // ---------------------------------------------
    // Adds country polygon layers and uses mockDestinations as temp travel data.
    // Later, mockDestinations will be replaced with backend API data.
    mapRef.current.on("load", () => {
        if (!mapRef.current) return; // null check insie load callback
        
        mapRef.current.addSource("countries", {
            type: "geojson",
            data: "/countries.geojson", // this file is in public folder, so it can be accessed directly
            promoteId: "ISO3166-1-Alpha-3", // setFeatureState required feature id, promoteId promotes a property into feature id
        });

        mapRef.current.addLayer({
            id: "country-fill",
            type: "fill",
            source: "countries",
            layout: {},
            paint: {
                "fill-color": [
                    "match",
                    ["get", "ISO3166-1-Alpha-3"],
                    ...mockDestinations.flatMap((destination) => [
                        destination.countryCode,
                        getColor(destination.travelScore),
                    ]),
                    "transparent", // default color for countries not in the mock data
                ],

                /* changes opacity when a country is hovered
                if feature-state hover is transformValueTypes, opacity becomes 0.75
                else remains 0.5 */
                "fill-opacity": [
                    "case",
                    ["boolean", ["feature-state", "hover"], false],
                    0.75,
                    0.5,
                ],
            },
        });

        mapRef.current.addLayer({
            id: "country-outline",
            type: "line",
            source: "countries",
            layout: {},
            paint: {
                "line-color": "#111827",
                "line-width": [
                    "case",
                    ["boolean", ["feature-state", "hover"], false],
                    1.5,
                    0.5,
                ]
            },
        });

        // helper function to set hovered country to false
        function clearHoveredCountry(): void {
            if (!mapRef.current) return;

            if (hoveredCountryIdRef.current !== null){
                mapRef.current.setFeatureState(
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

        // hover effect (polygon highlighting and tooltip display)
        mapRef.current.on(
            "mousemove", 
            "country-fill", 
            (event) => {
                if (!mapRef.current) return;

                // get the first country feature under the mouse
                const feature = event.features?.[0];

                // if no country feature, stop
                if (feature === undefined) return;

                // read country code from hovered GeoJSON feature
                const countryCode = feature.properties?.["ISO3166-1-Alpha-3"];

                // ensure country code is a string before using
                if (typeof countryCode !== "string") return;
                
                // if another country was previously hovered, remove its hover state first
                clearHoveredCountry();

                hoveredCountryIdRef.current = countryCode; // store currently hovered country code

                // apply hover state to the current country
                // activates fill and line-width changes
                mapRef.current.setFeatureState(
                {
                    source: "countries",
                    id: countryCode, // promoteId reads "ISO..."" as the feature ID
                },
                {
                    hover: true,
                }
                );

                // find matching destination data from mockDestinations
                const destination = findDestinationByCountryCode(countryCode);

                // if country not in mockDestinations, hide the tooltip
                if (destination === undefined) {
                    setTooltip(null);
                    return;
                }

                // change cursor to pointer to show that country is interactive
                mapRef.current.getCanvas().style.cursor = "pointer";

                // update React state so CountryTooltip appears near the mouse cursor
                setTooltip({
                    destination: destination,
                    x: event.point.x,
                    y: event.point.y,
                });
            }
        );

        mapRef.current.on("mouseleave", "country-fill", () => {
            if (!mapRef.current) return;

            // remove hover state from the last hovered country
            clearHoveredCountry();
            
            mapRef.current.getCanvas().style.cursor = ""; // reset cursor back to default
            setTooltip(null);  // hide tooltip
        });

        // click country polygon and go to destination dashboard page
        mapRef.current.on("click", "country-fill", (event) => {
            const feature = event.features?.[0];

            if (feature === undefined) return;

            const countryCode = feature.properties?.["ISO3166-1-Alpha-3"];

            if (typeof countryCode !== "string") return;

            const destination = findDestinationByCountryCode(countryCode);

            if (destination === undefined) return;

            navigate(`/destinations/${countryCode}`);
        });

    });
    // ----------------------------------------------

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  return (
    <div className="relative h-full w-full">
        <div className="h-full w-full" ref={mapContainerRef} />

        <AnimatePresence>
            {tooltip != null && (
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

export default MapView;