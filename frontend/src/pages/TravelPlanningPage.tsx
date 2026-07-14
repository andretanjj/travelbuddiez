import { useState } from "react";
import { Plane, Hotel, Search } from "lucide-react";

import { searchFlights, searchHotels } from "../services/travelApi";
import type {
  ActiveTravelTab,
  FlightResult,
  HotelResult,
} from "../types/travel";

function TravelPlanningPage() {
  const [activeTab, setActiveTab] = useState<ActiveTravelTab>("flights");

  // Flight search form states.
  // Current prototype uses airport / city codes because Duffel expects codes like SIN, HND, NRT, TYO.
  const [origin, setOrigin] = useState("SIN");
  const [destination, setDestination] = useState("HND");
  const [departureDate, setDepartureDate] = useState("2026-08-20");

  // Hotel search form states.
  // Current prototype uses city / airport codes because LiteAPI rates search accepts iataCode.
  const [hotelCity, setHotelCity] = useState("TYO");
  const [checkInDate, setCheckInDate] = useState("2026-08-20");
  const [checkOutDate, setCheckOutDate] = useState("2026-08-25");

  // Shared search input for flights and hotels.
  const [adults, setAdults] = useState(1);

  // Price alert states remain frontend-only for now.
  const [alertPrice, setAlertPrice] = useState("");
  const [hotelAlertPrice, setHotelAlertPrice] = useState("");

  // API result states.
  const [flights, setFlights] = useState<FlightResult[]>([]);
  const [hotels, setHotels] = useState<HotelResult[]>([]);

  // UI feedback states.
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const targetPrice = Number(alertPrice);
  const hotelTargetPrice = Number(hotelAlertPrice);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    // Prevent browser refresh when the form is submitted.
    event.preventDefault();

    setIsLoading(true);
    setErrorMessage("");

    try {
      if (activeTab === "flights") {
        // Calls backend GET /travel/flights/search.
        // Backend then tries Duffel first and falls back to mock data if needed.
        const flightResponse = await searchFlights({
          origin,
          destination,
          departureDate,
          adults,
        });

        setFlights(flightResponse.results);
      } else {
        // Calls backend GET /travel/hotels/search.
        // Backend then tries LiteAPI / Nuitee first and falls back to mock data if needed.
        const hotelResponse = await searchHotels({
          city: hotelCity,
          checkInDate,
          checkOutDate,
          adults,
        });

        setHotels(hotelResponse.results);
      }
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Unable to load travel planning results.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-2 text-3xl font-bold">Travel Planning</h1>

        <p className="text-slate-400">
          Search and compare available flights and hotels.
        </p>

        <p className="mb-8 mt-2 text-xs text-slate-500">
          Flight results are powered by Duffel. Hotel prices are powered by
          LiteAPI / Nuitee.
        </p>

        {/* Toggle buttons */}
        <div className="mb-6 flex gap-3">
          <button
            type="button"
            onClick={() => setActiveTab("flights")}
            className={`flex items-center gap-2 rounded-full border px-5 py-2 transition ${
              activeTab === "flights"
                ? "border-amber-500 bg-amber-500 text-slate-950"
                : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
            }`}
          >
            <Plane size={16} />
            Flights
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("hotels")}
            className={`flex items-center gap-2 rounded-full border px-5 py-2 transition ${
              activeTab === "hotels"
                ? "border-amber-500 bg-amber-500 text-slate-950"
                : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
            }`}
          >
            <Hotel size={16} />
            Hotels
          </button>
        </div>

        {/* Search form */}
        <form
          onSubmit={handleSearch}
          className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-5"
        >
          {activeTab === "flights" ? (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    From
                  </label>

                  <input
                    type="text"
                    value={origin}
                    onChange={(event) => setOrigin(event.target.value)}
                    required
                    placeholder="e.g. SIN for Singapore"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    To
                  </label>

                  <input
                    type="text"
                    value={destination}
                    onChange={(event) => setDestination(event.target.value)}
                    required
                    placeholder="e.g. HND for Tokyo Haneda"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Departure date
                  </label>

                  <input
                    type="date"
                    value={departureDate}
                    onChange={(event) => setDepartureDate(event.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Adults
                  </label>

                  <input
                    type="number"
                    min={1}
                    value={adults}
                    onChange={(event) => setAdults(Number(event.target.value))}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <p className="mt-3 text-xs text-slate-500">
                Prototype note: use airport or city codes for now, such as SIN,
                HND, NRT, TYO, or KUL. Search suggestions will be added later.
              </p>
            </>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Hotel destination
                  </label>

                  <input
                    type="text"
                    value={hotelCity}
                    onChange={(event) => setHotelCity(event.target.value)}
                    required
                    placeholder="e.g. TYO for Tokyo"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Check-in
                  </label>

                  <input
                    type="date"
                    value={checkInDate}
                    onChange={(event) => setCheckInDate(event.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Check-out
                  </label>

                  <input
                    type="date"
                    value={checkOutDate}
                    onChange={(event) => setCheckOutDate(event.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Adults
                  </label>

                  <input
                    type="number"
                    min={1}
                    value={adults}
                    onChange={(event) => setAdults(Number(event.target.value))}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <p className="mt-3 text-xs text-slate-500">
                Prototype note: use destination codes for now, such as TYO for
                Tokyo, SIN for Singapore, or KUL for Kuala Lumpur. Hotel names
                and ratings will be enriched later.
              </p>
            </>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="mt-5 flex items-center gap-2 rounded-xl bg-amber-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Search size={18} />
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {errorMessage && (
          <div className="mb-6 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
            {errorMessage}
          </div>
        )}

        {/* Flight price alert */}
        {activeTab === "flights" && (
          <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <label className="mb-2 block text-sm text-slate-400">
              Set flight price alert
            </label>

            <input
              type="number"
              placeholder="Notify me when flights are below this price"
              value={alertPrice}
              onChange={(event) => setAlertPrice(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
            />

            <p className="mt-2 text-xs text-slate-500">
              Prototype feature: alerts are checked against the current search
              results.
            </p>
          </div>
        )}

        {/* Hotel price alert */}
        {activeTab === "hotels" && (
          <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <label className="mb-2 block text-sm text-slate-400">
              Set hotel price alert
            </label>

            <input
              type="number"
              placeholder="Notify me when hotels are below this price per night"
              value={hotelAlertPrice}
              onChange={(event) => setHotelAlertPrice(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
            />

            <p className="mt-2 text-xs text-slate-500">
              Prototype feature: alerts are checked against the current search
              results.
            </p>
          </div>
        )}

        {/* Flights */}
        {activeTab === "flights" && (
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Available Flights</h2>

              <p className="text-sm text-slate-400">
                Sorted from lowest to highest price
              </p>
            </div>

            <div className="grid gap-4">
              {flights.map((flight) => {
                const isBelowTarget =
                  targetPrice > 0 && flight.price <= targetPrice;

                return (
                  <div
                    key={flight.id}
                    className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:flex-row md:items-center md:justify-between"
                  >
                    <div>
                      <h3 className="text-lg font-semibold">
                        {flight.city}, {flight.country}
                      </h3>

                      <p className="text-sm text-slate-400">
                        {flight.route}
                      </p>

                      <p className="mt-1 text-sm text-slate-400">
                        {flight.airline} · {flight.duration} · {flight.stops}
                      </p>

                      <p className="mt-1 text-sm text-slate-500">
                        Departure: {flight.departureDate}
                      </p>

                      {isBelowTarget && (
                        <p className="mt-3 text-sm text-green-400">
                          Price alert: This flight is within your budget!
                        </p>
                      )}
                    </div>

                    <div className="text-left md:text-right">
                      <p className="text-sm text-slate-400">from</p>

                      <p className="text-2xl font-bold text-amber-500">
                        {flight.currency} {flight.price}
                      </p>
                    </div>
                  </div>
                );
              })}

              {!isLoading && flights.length === 0 && (
                <p className="text-slate-400">
                  No flights found yet. Try searching SIN to HND.
                </p>
              )}
            </div>
          </section>
        )}

        {/* Hotels */}
        {activeTab === "hotels" && (
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Available Hotels</h2>

              <p className="text-sm text-slate-400">
                Sorted from lowest to highest price
              </p>
            </div>

            <div className="grid gap-4">
              {hotels.map((hotel) => {
                const isBelowTarget =
                  hotelTargetPrice > 0 && hotel.price <= hotelTargetPrice;

                return (
                  <div
                    key={hotel.id}
                    className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:flex-row md:items-center md:justify-between"
                  >
                    <div>
                      <h3 className="text-lg font-semibold">{hotel.name}</h3>

                      <p className="text-sm text-slate-400">
                        {hotel.city}, {hotel.country}
                      </p>

                      {/* Hide rating when provider metadata has not been enriched yet. */}
                      {hotel.rating > 0 && (
                        <p className="mt-1 text-sm text-slate-400">
                          Rating: {hotel.rating}/10
                        </p>
                      )}

                      <p className="mt-1 text-sm text-slate-500">
                        {hotel.checkInDate} → {hotel.checkOutDate}
                      </p>

                      {isBelowTarget && (
                        <p className="mt-3 text-sm text-green-400">
                          Price alert: This hotel is within your budget!
                        </p>
                      )}
                    </div>

                    <div className="text-left md:text-right">
                      <p className="text-sm text-slate-400">per night from</p>

                      <p className="text-2xl font-bold text-amber-500">
                        {hotel.currency} {hotel.price}
                      </p>
                    </div>
                  </div>
                );
              })}

              {!isLoading && hotels.length === 0 && (
                <p className="text-slate-400">
                  No hotels found yet. Try searching TYO.
                </p>
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default TravelPlanningPage;