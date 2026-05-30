import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

// OLD VERSION USING MOCK DATA
import { mockDestinations } from "../data/mockDestinations";

// NEW VERSION USING BACKEND API DATA: TO BE IMPLEMENTED LATER ONCE DATABASE IS IN PLAY
// import { getAllDestinations } from "../services/destinationApi";

import CountryTooltip from "./CountryTooltip.tsx";
import type { Destination } from "../types/country";

// stores data needed to display the tooltip (same as CountryTooltip)
interface TooltipState {
    destination: Destination;
    x: number;
    y: number;
}

// OLD VERSION: finds matching mock destination based on country code from GeoJSON
function findDestinationByCountryCode(countryCode: string): Destination | undefined {
    return mockDestinations.find(
        (destination: Destination) => destination.countryCode === countryCode
    );
}

// NEW VERSION: finds matching backend data country: implement later
/* function findDestinationByCountryCode(countryCode: string, destinations: Destination[]): Destination | undefined {
    return destinations.find(
        (destination: Destination) => destination.countryCode === countryCode
    );
} */

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

  // to be implemented later once database is countries.
  //const [destinations, setDestinations] = useState<Destination[]>([]);

  // allows this component to move to another page (DestinationDashboardPage)
  const navigate = useNavigate();

  // fetch backend destinations before creating map: to be implemented later once database is introduced
  /* useEffect(() => {
    async function fetchDestinations() {
        try {
            const data = await getAllDestinations();
            console.log("Backend destinations:", data);
            setDestinations(data);
        } catch (error) {
            console.error("Failed to fetch destinations:", error);
        }
    }

    fetchDestinations();
}, []); */

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
      zoom: 2.5,
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

                    //OLD VERSION USING mockDestinations
                    ...mockDestinations.flatMap((destination) => [
                        destination.countryCode,
                        getColor(destination.travelScore),
                    ]),
                    
                    // NEW VERSION USING backend: implement later
                    /* ...destinations.flatMap((destination) => {
                        // in case backend fails to calculate travelScore
                        if (destination.travelScore === undefined) {
                            return[];
                        }
                        return [
                            destination.countryCode,
                            getColor(destination.travelScore),
                        ];
                    }), */
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

                // OLD VERSION: find matching destination data from mockDestinations
                const destination = findDestinationByCountryCode(countryCode);

                // NEW VERSION: implement later when database is introduced
                // const destination = findDestinationByCountryCode(countryCode, destinations);

                // OLD VERSION: if country not in mockDestinations
                if (destination === undefined) {
                    setTooltip(null);
                    return;
                }

                // NEW VERSION: if country not in mockDestinations or backend fails to calculate travelScore, hide the tooltip
                if (destination === undefined || destination.travelScore === undefined) {
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

            // OLD VERSION: only test mock countries
            const destination = findDestinationByCountryCode(countryCode);

            if (destination === undefined) {
                console.log("No mock destination data for:", countryCode);
                return;
            }

            navigate(`/destinations/${countryCode}`);
        });

    });
    // ----------------------------------------------

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [navigate]);

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