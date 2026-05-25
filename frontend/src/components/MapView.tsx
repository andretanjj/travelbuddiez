import { useRef, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { mockDestinations } from "../data/mockDestinations";

function getColor(score: number){
    if (score >= 75) return "green";
    if (score >= 50) return "yellow";
    return "red";
}

function MapView() {
  const mapRef = useRef<mapboxgl.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

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
    // using mock data for now, will integrate with backend later
    mapRef.current.on("load", () => {
        if (!mapRef.current) return; // null check insie load callback
        
        mapRef.current.addSource("countries", {
            type: "geojson",
            data: "/countries.geojson", // this file is in public folder, so it can be accessed directly
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
                "fill-opacity": 0.5,
            },
        });

        mapRef.current.addLayer({
            id: "country-outline",
            type: "line",
            source: "countries",
            layout: {},
            paint: {
                "line-color": "#111827",
                "line-width": 0.5,
            },
        });
    });
    // ----------------------------------------------

    return () => {
      mapRef.current?.remove();
    };
  }, []);

  return <div className="h-full w-full" ref={mapContainerRef} />;
}

export default MapView;