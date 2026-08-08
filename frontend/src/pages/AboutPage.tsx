import {
    HiOutlineGlobeAlt,
    HiOutlineShieldCheck,
    HiOutlineCloud,
    HiOutlineNewspaper,
    HiOutlinePaperAirplane,
    HiOutlineBuildingOffice2,
    HiOutlineBellAlert,
    HiOutlineSparkles,
    HiOutlineBookmark,
} from "react-icons/hi2";


const FEATURES = [
    {
        title: "Interactive Travel Map",
        description:
            "Explore destinations around the world and quickly view travel scores, risk levels and general travel conditions.",
        icon: HiOutlineGlobeAlt,
    },
    {
        title: "Travel Safety Insights",
        description:
            "View destination risk levels, travel advisories and safety information to help you make more informed travel decisions.",
        icon: HiOutlineShieldCheck,
    },
    {
        title: "Weather Information",
        description:
            "Check destination weather information and conditions before planning your journey.",
        icon: HiOutlineCloud,
    },
    {
        title: "Travel News",
        description:
            "Stay informed with recent travel-related news that may affect your destination or travel plans.",
        icon: HiOutlineNewspaper,
    },
    {
        title: "Flight Search",
        description:
            "Search for available flight options based on your departure location, destination and travel dates.",
        icon: HiOutlinePaperAirplane,
    },
    {
        title: "Hotel Search",
        description:
            "Find hotel options for your destination and compare accommodation choices for your trip.",
        icon: HiOutlineBuildingOffice2,
    },
    {
        title: "Price Alerts",
        description:
            "Save flights or hotels and create price alerts to keep track of the travel options you are interested in.",
        icon: HiOutlineBellAlert,
    },
    {
        title: "AI Travel Assistant",
        description:
            "Get personalised travel recommendations, itinerary ideas, budget guidance and answers to travel-related questions.",
        icon: HiOutlineSparkles,
    },
    {
        title: "Saved AI Responses",
        description:
            "Save useful AI-generated travel plans and recommendations so you can easily refer back to them later.",
        icon: HiOutlineBookmark,
    },
];


const STEPS = [
    {
        number: "01",
        title: "Explore destinations",
        description:
            "Start with the Travel Map to compare destinations and view their travel scores, risk levels and general conditions.",
    },
    {
        number: "02",
        title: "View destination details",
        description:
            "Select a destination to view more detailed information such as weather, travel advisories and recent travel-related news.",
    },
    {
        number: "03",
        title: "Plan your journey",
        description:
            "Search for flights and hotels using your preferred destination, travel dates and number of travellers.",
    },
    {
        number: "04",
        title: "Save and track",
        description:
            "Log in to save flights and hotels and create price alerts for travel options you want to monitor.",
    },
    {
        number: "05",
        title: "Ask TravelBuddiez AI",
        description:
            "Enter your destination, dates, interests and concerns to receive personalised travel suggestions and planning assistance.",
    },
    {
        number: "06",
        title: "Save useful responses",
        description:
            "Bookmark helpful AI responses so you can revisit itineraries, recommendations and travel advice later.",
    },
];


export default function AboutPage() {
    return (
        <main className="min-h-screen bg-slate-950 text-white">
            {/* Hero */}
            <section className="px-4 pb-20 pt-32">
                <div className="mx-auto max-w-6xl text-center">
                    <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-400">
                        About TravelBuddiez
                    </p>

                    <h1 className="mx-auto mt-5 max-w-4xl text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
                        Plan smarter.
                        <span className="text-cyan-400"> Travel safer.</span>
                    </h1>

                    <p className="mx-auto mt-6 max-w-3xl text-base leading-8 text-slate-400 sm:text-lg">
                        TravelBuddiez is a travel planning and safety
                        platform that brings destination insights, travel
                        information, planning tools and AI-powered
                        assistance together in one place.
                    </p>
                </div>
            </section>

            {/* What is TravelBuddiez */}
            <section className="px-4 py-20">
                <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-2 lg:items-center">
                    <div>
                        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">
                            Our Purpose
                        </p>

                        <h2 className="mt-4 text-3xl font-bold">
                            Making travel planning simpler
                        </h2>

                        <p className="mt-5 leading-7 text-slate-400">
                            Planning a trip often requires travellers to
                            visit multiple websites for safety information,
                            weather, travel advisories, news, flights,
                            hotels and recommendations.
                        </p>

                        <p className="mt-4 leading-7 text-slate-400">
                            TravelBuddiez aims to simplify this process by
                            bringing these resources together into a single
                            platform. Users can research destinations,
                            understand current travel conditions, plan
                            flights and accommodation, and receive
                            personalised assistance from the TravelBuddiez
                            AI assistant.
                        </p>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-slate-900 p-8">
                        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10">
                            <HiOutlineGlobeAlt className="h-7 w-7 text-cyan-400" />
                        </div>

                        <h3 className="mt-6 text-2xl font-semibold">
                            One platform for your journey
                        </h3>

                        <p className="mt-4 leading-7 text-slate-400">
                            From researching a destination to checking
                            travel conditions, searching for flights and
                            hotels, tracking prices and planning with AI,
                            TravelBuddiez supports travellers throughout
                            the planning process.
                        </p>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="border-y border-white/10 bg-slate-900/50 px-4 py-20">
                <div className="mx-auto max-w-6xl">
                    <div className="max-w-2xl">
                        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">
                            Key Features
                        </p>

                        <h2 className="mt-4 text-3xl font-bold">
                            Everything you need to plan with confidence
                        </h2>

                        <p className="mt-4 leading-7 text-slate-400">
                            TravelBuddiez combines destination information
                            with planning and personalised tools to help
                            users make more informed travel decisions.
                        </p>
                    </div>

                    <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                        {FEATURES.map((feature) => {
                            const Icon = feature.icon;

                            return (
                                <article
                                    key={feature.title}
                                    className="
                                        rounded-2xl border border-white/10
                                        bg-slate-950 p-6
                                        transition
                                        hover:border-cyan-400/30
                                        hover:bg-slate-900
                                    "
                                >
                                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10">
                                        <Icon className="h-6 w-6 text-cyan-400" />
                                    </div>

                                    <h3 className="mt-5 text-lg font-semibold">
                                        {feature.title}
                                    </h3>

                                    <p className="mt-3 text-sm leading-6 text-slate-400">
                                        {feature.description}
                                    </p>
                                </article>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* How to use */}
            <section className="px-4 py-20">
                <div className="mx-auto max-w-6xl">
                    <div className="text-center">
                        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">
                            How It Works
                        </p>

                        <h2 className="mt-4 text-3xl font-bold">
                            Start planning in a few simple steps
                        </h2>

                        <p className="mx-auto mt-4 max-w-2xl leading-7 text-slate-400">
                            Explore destinations, plan your trip and use
                            TravelBuddiez tools to keep useful travel
                            information in one place.
                        </p>
                    </div>

                    <div className="mt-12 grid gap-5 md:grid-cols-2">
                        {STEPS.map((step) => (
                            <article
                                key={step.number}
                                className="
                                    flex gap-5 rounded-2xl
                                    border border-white/10
                                    bg-slate-900 p-6
                                "
                            >
                                <div className="flex h-11 min-w-11 items-center justify-center rounded-xl bg-cyan-500/10 text-sm font-bold text-cyan-400">
                                    {step.number}
                                </div>

                                <div>
                                    <h3 className="text-lg font-semibold">
                                        {step.title}
                                    </h3>

                                    <p className="mt-2 text-sm leading-6 text-slate-400">
                                        {step.description}
                                    </p>
                                </div>
                            </article>
                        ))}
                    </div>
                </div>
            </section>

            {/* AI section */}
            <section className="px-4 pb-20">
                <div
                    className="
                        mx-auto max-w-6xl overflow-hidden
                        rounded-3xl border border-cyan-400/20
                        bg-gradient-to-br
                        from-cyan-500/10
                        via-slate-900
                        to-slate-900
                        p-8 sm:p-10
                    "
                >
                    <div className="max-w-3xl">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/15">
                            <HiOutlineSparkles className="h-6 w-6 text-cyan-400" />
                        </div>

                        <h2 className="mt-6 text-3xl font-bold">
                            Meet the TravelBuddiez AI Assistant
                        </h2>

                        <p className="mt-4 leading-7 text-slate-300">
                            The AI Assistant helps users make sense of their
                            travel options by combining their trip details,
                            preferences and available TravelBuddiez data.
                            Users can ask about destinations, itineraries,
                            budgeting, flights, hotels, safety concerns and
                            other travel-related topics.
                        </p>

                        <p className="mt-4 leading-7 text-slate-400">
                            Useful AI responses can also be saved for future
                            reference, making it easier to return to travel
                            plans and recommendations later.
                        </p>
                    </div>
                </div>
            </section>

            {/* Disclaimer */}
            <section className="px-4 pb-24">
                <div className="mx-auto max-w-6xl rounded-2xl border border-white/10 bg-slate-900 p-6">
                    <h2 className="font-semibold">
                        Important information
                    </h2>

                    <p className="mt-3 text-sm leading-6 text-slate-400">
                        TravelBuddiez provides travel information and
                        recommendations for planning purposes. Travel
                        conditions, prices, availability, weather, news and
                        advisories may change over time. Users should verify
                        important information with official sources and
                        booking providers before making travel decisions.
                    </p>
                </div>
            </section>
        </main>
    );
}