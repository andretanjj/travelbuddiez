import './Home.css'

function Home() {
    return (
        <section className="hero">
            <div className="hero-content">
            <h1>TravelBuddiez</h1>
            <p className='tagline'>One Stop to all your Travel Needs</p>

            <p className='subtitle'>
                Plan smarter with destination insights, weather and travel condition updates. Your ultimate travel companion for unforgettable journeys.
            </p>

            <button className="hero-button" onClick={() => window.location.href = '/map'}>Explore Map</button>
            </div>
        </section>
    )
}

export default Home;