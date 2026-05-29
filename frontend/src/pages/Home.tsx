import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "motion/react";
import { useNavigate } from "react-router-dom";
import { FaPlane } from "react-icons/fa";
import GlobeBackground from "../components/GlobeBackground";

function Home() {
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const timer = setTimeout(() => { 
            setLoading(false);
        }, 1800);
        return () => clearTimeout(timer);
    }, []);
    return (
        <div className="relative min-h-screen bg-black">
            <section
                className="
                    relative isolate min-h-[calc(100vh-60px)] overflow-hidden
                    flex justify-center items-center bg-slate-950 px-5 py-10 text-center
                "
            >
                <GlobeBackground />

                <div className="relative z-10 w-full max-w-3xl">
                    <h1
                        className="mb-5 font-['Playfair_Display'] text-2xl font-semibold text-white"
                        style={{
                            textShadow: "0 2px 4px rgba(0, 0, 0, 0.8), 0 0 14px rgba(0, 0, 0, 0.67)",
                        }}
                    >
                        TravelBuddiez
                    </h1>

                    <p
                        className="mb-10 font-[Arial] text-4xl text-white [font-variant:small-caps]"
                        style={{
                            textShadow: "0 2px 4px rgba(0, 0, 0, 0.8), 0 0 12px rgba(0, 0, 0, 0.67)",
                        }}
                    >
                        One Stop to all your Travel Needs
                    </p>

                    <p
                        className="
                            mx-auto mb-8 max-w-2xl text-base font-medium leading-relaxed text-[#ebf1ff]
                        "
                        style={{
                            textShadow: "0 2px 4px rgba(5, 0, 0, 0.85), 0 0 10px rgba(0, 0, 0, 0.85)",
                        }}
                    >
                        Plan smarter with destination insights, weather and travel condition updates.
                        Your ultimate travel companion for unforgettable journeys.
                    </p>

                    <button
                        onClick={() => navigate("/map")}
                        className="
                            rounded-lg border border-black bg-blue-600/80 px-7 py-3.5
                            font-['Manrope'] font-bold text-white shadow-lg transition-colors
                            hover:bg-blue-700
                        "
                    >
                        Explore Map
                    </button>
                </div>
            </section>
            <AnimatePresence>
                {loading && (
                    <motion.section 
                        key="loading"
                        initial={{ opacity: 1 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1.67, ease: "easeInOut" }}
                        className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden bg-black"
                    >
                        <motion.h1  
                            initial={{ opacity: 0, y: 15 }}
                            animate={{
                                opacity: [0, 1, 1, 0], y: [15, 0, 0, 0],
                            }}
                            transition={{
                                duration: 1.67, times:[0, 0.3, 0.5, 1], ease: "easeOut",
                            }}
                            className="font-['Playfair_Display'] text-5xl font-semibold text-white md:text-7xl"
                        >
                            TravelBuddiez
                        </motion.h1>
                        <motion.div
                            initial={{
                                x: "-65vw", y: 0, opacity: 0,
                            }}
                            animate={{
                                x: "65vw", y: 0, opacity: [0, 1, 1, 0],
                            }}
                            transition={{
                                duration: 1.67, delay: 0.5, ease: "easeInOut",
                            }}
                            className="absolute text-5xl text-white md:text-7xl"
                        >
                            <FaPlane />
                        </motion.div>
                    </motion.section>
                )}
            </AnimatePresence>
        </div>
    );
}

export default Home;