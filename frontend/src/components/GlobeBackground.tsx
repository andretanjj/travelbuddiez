import { useEffect, useRef } from "react";
import Globe from "react-globe.gl";
import type { GlobeMethods } from "react-globe.gl";

function GlobeBackground() {
    const globeRef = useRef<GlobeMethods | undefined>(undefined);

    useEffect(() => {
        if (!globeRef.current) return;

        globeRef.current.pointOfView(
            {
                lat: 10,
                lng: 100,
                altitude: 2.5,
            },
            1000
        );

        const controls = globeRef.current.controls();
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.8;
        controls.enableZoom = true;
    }, []);

    return (
        <div className="absolute inset-0 z-0 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-black" />

            <div className="absolute left-1/2 top-1/2 h-[1000px] w-[1000px] -translate-x-1/2 -translate-y-1/2 opacity-90">
                <Globe
                    ref={globeRef}
                    width={1000}
                    height={1000}
                    backgroundColor="rgba(0, 0, 0, 0)"
                    globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                    bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
                    showAtmosphere={true}
                    atmosphereColor="lightskyblue"
                    enablePointerInteraction={true}
                />
            </div>
        </div>
    );
}

export default GlobeBackground;