import earth from "../assets/earth.jpeg"

function Home() {
    return (
        <section 
            className="
                min-h-[calc(100vh-60px)] flex justify-center items-center bg-cover bg-center px-5 py-10 text-center"
            style={{
                backgroundImage: `linear-gradient(rgba(255,255,255,0.15), rgba(255,255,255,0.15)), url(${earth})`,
            }}
        >
            <div className="w-full max-w-3xl">
                <h1
                    className="
                        mb-5 font-['Playfair_Display'] text-2xl font-semibold text-white"
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
                        mx-auto mb-8 max-w-2xl text-base font-medium leading-relaxed text-[#ebf1ff]"
                    style={{
                        textShadow: "0 2px 4px rgba(5, 0, 0, 0.85), 0 0 10px rgba(0, 0, 0, 0.85)",
                    }}
                >
                    Plan smarter with destination insights, weather and travel condition updates. Your ultimate travel companion for unforgettable journeys.
                </p>

                <button 
                    onClick={() => window.location.href = '/map'}
                    className="rounded-lg border border-black bg-blue-600/80 px-7 py-3.5 font-['Manrope'] font-bold text-white shadow-lg transition-colors hover:bg-blue-700" 
                >
                    Explore Map
                </button>
            </div>
        </section>
    );
}

export default Home;