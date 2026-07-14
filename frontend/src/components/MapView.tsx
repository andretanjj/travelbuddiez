import { useRef, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "motion/react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

// OLD VERSION USING MOCK DATA
// import { mockDestinations } from "../data/mockDestinations";

// NEW VERSION USING backend
import { getAllDestinations } from "../services/destinationApi";

import CountryTooltip from "./CountryTooltip.tsx";
import type { MapDestination } from "../types/country";
import { FaGlobeAsia } from "react-icons/fa";
import { travelFacts } from "../data/travelFacts";

// stores data needed to display the tooltip (same as CountryTooltip)
interface TooltipState {
    destination: MapDestination;
    x: number;
    y: number;
}

// OLD VERSION: finds matching mock destination based on country code from GeoJSON
/* function findDestinationByCountryCode(countryCode: string): Destination | undefined {
    return mockDestinations.find(
        (destination: Destination) => destination.countryCode === countryCode
    );
} */

// NEW VERSION: finds matching backend data country
function findDestinationByCountryCode(countryCode: string, destinations: MapDestination[]): MapDestination | undefined {
    return destinations.find(
        (destination: MapDestination) => destination.countryCode === countryCode
    );
}

// convert travel score into map color
function getColor(score: number): string {
    if (score >= 75) return "#29bd29";
    else if (score >= 50) return "#ffff00";
    return "#f32e2e";
}


// this is for countryCodes with "-99"
function makeCountryCode(countryCode: string, countryName: string): string {
    if (countryCode !== "-99") {
        return countryCode;
    }

    return countryName
        .toUpperCase()
        .replace(/[^A-Z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
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

    // using advisory-based map data from backend
    const [destinations, setDestinations] = useState<MapDestination[]>([]);

    // loading states for backend data and Mapbox
    const [isDataLoading, setIsDataLoading] = useState(true);
    const [isMapLoading, setIsMapLoading] = useState(true);

    // randomly selects the first travel fact shown on the loading screen
    const [factIndex, setFactIndex] = useState(() =>
        Math.floor(Math.random() * travelFacts.length)
    );

    const isLoading = isDataLoading || isMapLoading;

    // allows this component to move to another page (DestinationDashboardPage)
    const navigate = useNavigate();

    // fetch advisory-based map data from backend. 
    // this gives MapView the mapScore used for country colours and tooltip
    useEffect(() => {
        async function fetchDestinations() {
            try {
                const data = await getAllDestinations();
                console.log("Backend destinations:", data);
                setDestinations(data);
            } catch (error) {
                console.error("Failed to fetch destinations:", error);
            } finally {
                setIsDataLoading(false);
            }
        }

        fetchDestinations();
    }, []);

    // changes the fun fact every 6.7 seconds while the loading screen is visible
    useEffect(() => {
        if (!isLoading || travelFacts.length <= 1) return;

        const interval = window.setInterval(() => {
            setFactIndex((currentIndex) => {
                let nextIndex = currentIndex;

                while (nextIndex === currentIndex) {
                    nextIndex = Math.floor(Math.random() * travelFacts.length);
                }

                return nextIndex;
            });
        }, 6700);

        return () => window.clearInterval(interval);
    }, [isLoading]);

    useEffect(() => {

        if (mapContainerRef.current === null) return;
        if (destinations.length === 0) return;

        mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

        // mapbox map instance
        mapRef.current = new mapboxgl.Map({
            container: mapContainerRef.current,
            style: 'mapbox://styles/mapbox/standard',
            config: {
                basemap: { theme: "monochrome" },
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
                        /* ...mockDestinations.flatMap((destination) => [
                            destination.countryCode,
                            getColor(destination.travelScore),
                        ]), */

                        // NEW VERSION USING advisory backend
                        ...destinations.flatMap((destination) => {
                            // if no mapScore, dont color the country
                            if (destination.mapScore === null || destination.mapScore === undefined) {
                                return [];
                            }
                            return [
                                destination.countryCode,
                                getColor(destination.mapScore),
                            ];
                        }),
                        "transparent", // default color for countries without backend mapScore
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

                if (hoveredCountryIdRef.current !== null) {
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
                    const rawCountryCode = feature.properties?.["ISO3166-1-Alpha-3"];
                    const countryName = feature.properties?.["name"];

                    if (typeof rawCountryCode !== "string") return;
                    if (typeof countryName !== "string") return;

                    const countryCode = makeCountryCode(rawCountryCode, countryName);

                    // if another country was previously hovered, remove its hover state first
                    clearHoveredCountry();

                    hoveredCountryIdRef.current = rawCountryCode; // store currently hovered country code

                    // apply hover state to the current country
                    // activates fill and line-width changes
                    mapRef.current.setFeatureState(
                        {
                            source: "countries",
                            id: rawCountryCode, // promoteId reads "ISO..."" as the feature ID
                        },
                        {
                            hover: true,
                        }
                    );

                    // OLD VERSION: find matching destination data from mockDestinations
                    // const destination = findDestinationByCountryCode(countryCode);

                    // NEW VERSION
                    const destination = findDestinationByCountryCode(countryCode, destinations);

                    // OLD VERSION: if country not in mockDestinations
                    /* if (destination === undefined) {
                        setTooltip(null);
                        return;
                    } */

                    // NEW VERSION: if country not in mockDestinations or backend fails to calculate travelScore, hide the tooltip
                    if (destination === undefined || destination.mapScore === undefined || destination.mapScore === null) {
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

                const rawCountryCode = feature.properties?.["ISO3166-1-Alpha-3"];
                const countryName = feature.properties?.["name"];

                if (typeof rawCountryCode !== "string") return;
                if (typeof countryName !== "string") return;

                const countryCode = makeCountryCode(rawCountryCode, countryName);

                // NEW VERSION
                const destination = findDestinationByCountryCode(countryCode, destinations);

                // If the country is not returned by backend /destinations,
                // do not navigate to dashboard.
                if (destination === undefined) {
                    console.log("No backend map data for:", countryCode);
                    return;
                }

                navigate(`/destinations/${countryCode}`);
            });

            // hide the loading overlay only after the map and custom layers are ready
            setIsMapLoading(false);

        });
        // ----------------------------------------------

        return () => {
            mapRef.current?.remove();
            mapRef.current = null;
        };
    }, [destinations, navigate]);

    return (
        <div className="relative h-full w-full">
            <div className="h-full w-full" ref={mapContainerRef} />

            <AnimatePresence>
                {isLoading && (
                    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950 px-6 text-center">
                        <FaGlobeAsia className="animate-spin text-6xl text-amber-500 [animation-duration:3s]" />

                        <p className="mt-5 text-base font-semibold text-white">
                            Loading travel map...
                        </p>

                        <p className="mt-1 text-sm text-white/60">
                            Preparing global travel conditions
                        </p>

                        <div className="mt-7 max-w-md rounded-2xl border border-white/10 bg-white/10 px-6 py-4 backdrop-blur-sm">
                            <p className="text-xs font-semibold uppercase tracking-widest text-amber-400">
                                Did you know?
                            </p>

                            <p className="mt-2 text-sm leading-6 text-white/80">
                                {travelFacts[factIndex]}
                            </p>
                        </div>
                    </div>
                )}
            </AnimatePresence>

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