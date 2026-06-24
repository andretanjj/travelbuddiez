import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useScroll, useTransform } from "motion/react";
import { useNavigate } from "react-router-dom";
import { IoIosAirplane } from "react-icons/io";
import { FiGlobe, FiMapPin, FiInfo, FiNavigation } from "react-icons/fi";

/* Star background from the uploaded landing page */
function StarField() {
    const stars = useRef<{ x: number; y: number; r: number; o: number }[]>([]);

    if (stars.current.length === 0) {
        for (let i = 0; i < 160; i++) {
            stars.current.push({
                x: Math.random() * 100,
                y: Math.random() * 100,
                r: Math.random() * 1.4 + 0.3,
                o: Math.random() * 0.6 + 0.2,
            });
        }
    }

    return (
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
            {stars.current.map((star, index) => (
                <div
                    key={index}
                    className="absolute rounded-full bg-white"
                    style={{
                        left: `${star.x}%`,
                        top: `${star.y}%`,
                        width: star.r * 2,
                        height: star.r * 2,
                        opacity: star.o,
                    }}
                />
            ))}
        </div>
    );
}

/* Globe from the uploaded landing page */
function GlobeHero() {
    return (
        <div className="relative flex h-[330px] w-[330px] select-none items-center justify-center md:h-[480px] md:w-[480px]">
            <div
                className="absolute inset-0 rounded-full"
                style={{
                    background:
                        "radial-gradient(circle, rgba(80,140,255,0.18) 55%, transparent 72%)",
                    transform: "scale(1.28)",
                }}
            />

            <div
                className="absolute inset-0 rounded-full"
                style={{
                    background:
                        "radial-gradient(circle, transparent 48%, rgba(100,180,255,0.12) 60%, transparent 70%)",
                    transform: "scale(1.14)",
                }}
            />

            <motion.div
                className="absolute inset-0 rounded-full"
                style={{
                    border: "1px solid rgba(255,255,255,0.08)",
                    transform: "rotateX(72deg) scale(1.18)",
                }}
                animate={{ rotate: 360 }}
                transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
            >
                <div
                    className="absolute rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(212,168,83,0.8)]"
                    style={{
                        width: 8,
                        height: 8,
                        top: -4,
                        left: "50%",
                        marginLeft: -4,
                    }}
                />
            </motion.div>

            <motion.div
                className="absolute inset-0 rounded-full"
                style={{
                    border: "1px solid rgba(255,255,255,0.05)",
                    transform: "rotateX(72deg) rotateZ(60deg) scale(1.24)",
                }}
                animate={{ rotate: -360 }}
                transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
            >
                <div
                    className="absolute rounded-full bg-blue-400 shadow-[0_0_6px_rgba(96,165,250,0.7)]"
                    style={{
                        width: 6,
                        height: 6,
                        top: -3,
                        left: "50%",
                        marginLeft: -3,
                    }}
                />
            </motion.div>

            <motion.div
                className="relative z-10 h-[285px] w-[285px] overflow-hidden rounded-full md:h-[420px] md:w-[420px]"
                animate={{ rotate: 360 }}
                transition={{ duration: 80, repeat: Infinity, ease: "linear" }}
            >
                <img
                    src="https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1000&h=1000&fit=crop&auto=format"
                    alt="Earth from space"
                    className="h-full w-full object-cover"
                    style={{ transform: "scale(1.05)" }}
                />

                <div
                    className="absolute inset-0 rounded-full"
                    style={{
                        background:
                            "radial-gradient(circle at 35% 30%, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0.04) 40%, transparent 65%)",
                    }}
                />

                <div
                    className="absolute inset-0 rounded-full"
                    style={{
                        background:
                            "radial-gradient(circle at 75% 70%, rgba(0,0,20,0.55) 0%, transparent 55%)",
                    }}
                />
            </motion.div>

            <div
                className="pointer-events-none absolute z-20 h-[285px] w-[285px] rounded-full md:h-[420px] md:w-[420px]"
                style={{
                    boxShadow:
                        "inset 0 0 40px 8px rgba(80,140,255,0.18), 0 0 60px 20px rgba(60,120,255,0.12)",
                }}
            />

            <motion.div
                className="
                    absolute bottom-8 left-0 z-30 flex items-center gap-2 rounded-full
                    border border-white/10 bg-slate-950/80 px-4 py-2 text-xs font-medium
                    text-white shadow-lg backdrop-blur-md md:-left-12
                "
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.2, duration: 0.8 }}
            >
                <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
                Live destination insights
            </motion.div>

            <motion.div
                className="
                    absolute right-0 top-10 z-30 flex items-center gap-2 rounded-full
                    border border-white/10 bg-slate-950/80 px-4 py-2 text-xs font-medium
                    text-white shadow-lg backdrop-blur-md md:-right-10
                "
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.5, duration: 0.8 }}
            >
                <FiMapPin className="text-yellow-400" />
                Selected destinations
            </motion.div>
        </div>
    );
}

function Footer() {
    const navigate = useNavigate();

    return (
        <footer className="relative z-10 border-t border-white/10 bg-[#070b16] px-6 py-12 text-slate-300">
            <div className="mx-auto max-w-7xl">
                <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
                    <div>
                        <div className="mb-6 flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#d9964a] text-black">
                                <FiGlobe className="h-5 w-5" />
                            </div>

                            <h2
                                className="font-['Playfair_Display'] text-2xl font-bold text-white"
                            >
                                Travel<span className="text-[#d9964a]">Buddiez</span>
                            </h2>
                        </div>

                        <p className="max-w-sm text-base leading-relaxed text-blue-200/75">
                            Connecting curious travellers across every time zone, terrain,
                            and cultural border.
                        </p>

                        <div className="mt-8 flex gap-4">
                            <a
                                href="#"
                                className="flex h-12 w-12 items-center justify-center rounded-full border border-white/10 text-blue-200/70 transition hover:border-white/20 hover:text-white"
                            >
                                IG
                            </a>

                            <a
                                href="#"
                                className="flex h-12 w-12 items-center justify-center rounded-full border border-white/10 text-blue-200/70 transition hover:border-white/20 hover:text-white"
                            >
                                X
                            </a>

                            <a
                                href="#"
                                className="flex h-12 w-12 items-center justify-center rounded-full border border-white/10 text-blue-200/70 transition hover:border-white/20 hover:text-white"
                            >
                                FB
                            </a>
                        </div>
                    </div>

                    <div>
                        <h3 className="mb-6 text-lg font-bold text-white">Explore</h3>

                        <div className="flex flex-col gap-4 text-blue-200/75">
                            <button
                                onClick={() => navigate("/map")}
                                className="w-fit text-left transition hover:text-white"
                            >
                                Travel Map
                            </button>

                            <button
                                onClick={() => navigate("/planning")}
                                className="w-fit text-left transition hover:text-white"
                            >
                                Trip Planning
                            </button>

                            <button
                                onClick={() => navigate("/about")}
                                className="w-fit text-left transition hover:text-white"
                            >
                                About
                            </button>
                        </div>
                    </div>

                    <div>
                        <h3 className="mb-6 text-lg font-bold text-white">Company</h3>

                        <div className="flex flex-col gap-4 text-blue-200/75">
                            <p className="w-fit">About Us</p>

                            <p className="w-fit">Contact Us</p>

                            <p className="w-fit">Safety</p>

                            <p className="w-fit">Privacy</p>

                            <p className="w-fit">Terms</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-14 flex flex-col gap-4 border-t border-white/10 pt-8 text-sm text-blue-200/75 md:flex-row md:items-center md:justify-between">
                <p>© 2026 TravelBuddiez. All rights reserved.</p>

                <p className="font-mono tracking-wide">
                    Travel Safe, Travel Smart.
                </p>
            </div>
        </footer >
    );
}

function Home() {
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const heroRef = useRef<HTMLDivElement>(null);

    const { scrollYProgress } = useScroll({
        target: heroRef,
        offset: ["start start", "end start"],
    });

    const globeY = useTransform(scrollYProgress, [0, 1], [0, 60]);
    const textY = useTransform(scrollYProgress, [0, 1], [0, -40]);

    useEffect(() => {
        const timer = setTimeout(() => {
            setLoading(false);
        }, 1800);

        return () => clearTimeout(timer);
    }, []);

    return (
        <div className="relative min-h-screen bg-[#080c18] text-white">
            <section
                ref={heroRef}
                className="
                    relative min-h-[calc(100vh-60px)] overflow-hidden pt-16
                    flex flex-col items-center justify-center
                "
            >
                <StarField />

                <div
                    className="absolute inset-0"
                    style={{
                        background:
                            "radial-gradient(ellipse 80% 80% at 50% 60%, rgba(20,30,60,0.9) 0%, #080c18 70%)",
                    }}
                />

                <div
                    className="pointer-events-none absolute inset-0"
                    style={{
                        background:
                            "radial-gradient(ellipse 40% 30% at 15% 40%, rgba(100,80,200,0.06) 0%, transparent 60%), radial-gradient(ellipse 35% 25% at 85% 65%, rgba(200,105,79,0.05) 0%, transparent 60%)",
                    }}
                />

                <div
                    className="
                        relative z-10 mx-auto grid w-full max-w-7xl grid-cols-1
                        items-center gap-12 px-6 py-16 lg:grid-cols-2
                    "
                >
                    <motion.div style={{ y: textY }} className="text-center lg:text-left">
                        <motion.div
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                        >
                            <span
                                className="
                                    mb-7 inline-flex items-center gap-2 rounded-full border
                                    border-yellow-400/25 bg-yellow-400/5 px-4 py-2 text-xs
                                    uppercase tracking-widest text-yellow-400
                                "
                            >
                                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-yellow-400" />
                                Your one-stop travel companion
                            </span>
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 28 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                                duration: 0.9,
                                delay: 0.1,
                                ease: [0.16, 1, 0.3, 1],
                            }}
                            className="
                                mb-6 text-5xl font-bold leading-[1.06] tracking-tight
                                text-white md:text-6xl xl:text-7xl
                            "
                            style={{ fontFamily: "'Playfair Display', serif" }}
                        >
                            One stop for {" "}
                            <span
                                className="whitespace-nowrap bg-clip-text text-transparent"
                                style={{
                                    backgroundImage:
                                        "linear-gradient(135deg, #d4a853 0%, #c8694f 60%, #d4a853 100%)",
                                }}
                            >
                                all your
                            </span>
                            <br />
                            travel needs.
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                                duration: 0.8,
                                delay: 0.22,
                                ease: [0.16, 1, 0.3, 1],
                            }}
                            className="
                                mx-auto mb-10 max-w-md text-base leading-relaxed text-slate-300
                                md:text-lg lg:mx-0
                            "
                        >
                            Plan smarter with destination insights, live weather, and travel condition
                            updates. Explore the world with confidence using TravelBuddiez.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                                duration: 0.7,
                                delay: 0.42,
                                ease: [0.16, 1, 0.3, 1],
                            }}
                            className="flex flex-col items-center justify-center gap-3 sm:flex-row lg:justify-start"
                        >
                            <button
                                onClick={() => navigate("/map")}
                                className="
                                    flex items-center gap-2 rounded-full bg-blue-600 px-7 py-3.5
                                    text-sm font-semibold text-white shadow-xl shadow-blue-600/25
                                    transition-all hover:bg-blue-500 active:scale-95
                                "
                            >
                                <FiGlobe className="h-4 w-4" />
                                Explore Map
                            </button>

                            <button
                                onClick={() => navigate("/planning")}
                                className="
                                    rounded-full border border-white/10 px-6 py-3.5 text-sm
                                    font-medium text-slate-300 transition-all hover:border-white/20
                                    hover:text-white
                                "
                            >
                                Travel Planning
                            </button>
                        </motion.div>
                    </motion.div>

                    <motion.div
                        className="flex items-center justify-center"
                        style={{ y: globeY }}
                        initial={{ opacity: 0, scale: 0.88 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{
                            duration: 1.1,
                            delay: 0.15,
                            ease: [0.16, 1, 0.3, 1],
                        }}
                    >
                        <GlobeHero />
                    </motion.div>
                </div>
            </section>

            <Footer />

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
                                opacity: [0, 1, 1, 0],
                                y: [15, 0, 0, 0],
                            }}
                            transition={{
                                duration: 1.67,
                                times: [0, 0.3, 0.5, 1],
                                ease: "easeOut",
                            }}
                            className="font-['Playfair_Display'] text-5xl font-semibold text-white md:text-7xl"
                        >
                            TravelBuddiez
                        </motion.h1>

                        <motion.div
                            initial={{
                                x: "-40vw",
                                y: "15vh",
                                opacity: 0,
                                rotate: -15,
                                scale: 0.9,
                            }}
                            animate={{
                                x: "50vw",
                                y: "-15vh",
                                opacity: [0, 1, 1, 0],
                                scale: [0.7, 1.3, 1.8, 2.3, 2.8],
                            }}
                            transition={{
                                duration: 2,
                                delay: 0.5,
                                ease: "easeInOut",
                                times: [0, 0.25, 0.5, 0.75, 1],
                            }}
                            className="absolute text-5xl text-white drop-shadow-[0_0_18px_rgba(255,255,255,0.55)] md:text-7xl"
                        >
                            <IoIosAirplane />
                        </motion.div>
                    </motion.section>
                )}
            </AnimatePresence>
        </div>
    );
}

export default Home;