import { useMemo, useState } from "react";
import { Plane, Hotel, Search } from "lucide-react";
import { mockFlights, mockHotels } from "../data/travelMockData";

type ActiveTab = "flights" | "hotels";

function TravelPlanningPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("flights");
  const [searchTerm, setSearchTerm] = useState("");
  const [alertPrice, setAlertPrice] = useState("");
  const [hotelAlertPrice, setHotelAlertPrice] = useState("");

  const filteredFlights = useMemo(() => {
    return mockFlights
      .filter((flight) => {
        const searchText = `${flight.city} ${flight.country}`.toLowerCase();
        return searchText.includes(searchTerm.toLowerCase());
      })
      .sort((a, b) => a.price - b.price);
  }, [searchTerm]);

  const filteredHotels = useMemo(() => {
    return mockHotels
      .filter((hotel) => {
        const searchText =
          `${hotel.name} ${hotel.city} ${hotel.country}`.toLowerCase();

        return searchText.includes(searchTerm.toLowerCase());
      })
      .sort((a, b) => a.price - b.price);
  }, [searchTerm]);

  const targetPrice = Number(alertPrice);
  const hotelTargetPrice = Number(hotelAlertPrice);


  return (
    <main className="min-h-screen bg-slate-950 text-white px-6 py-10">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Travel Planning</h1>

        <p className="text-slate-400 mb-8">
          Search and compare available flights and hotels.
        </p>

        {/* Toggle buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setActiveTab("flights")}
            className={`flex items-center gap-2 px-5 py-2 rounded-full border transition ${
              activeTab === "flights"
                ? "bg-amber-500 text-slate-950 border-amber-500"
                : "bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500"
            }`}
          >
            <Plane size={16} />
            Flights
          </button>

          <button
            onClick={() => setActiveTab("hotels")}
            className={`flex items-center gap-2 px-5 py-2 rounded-full border transition ${
              activeTab === "hotels"
                ? "bg-amber-500 text-slate-950 border-amber-500"
                : "bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500"
            }`}
          >
            <Hotel size={16} />
            Hotels
          </button>
        </div>

        {/* Search bar */}
        <div className="relative mb-6">
          <Search
            size={18}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          />

          <input
            type="text"
            placeholder={
              activeTab === "flights"
                ? "Search flights by destination..."
                : "Search hotels by destination..."
            }
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-3 pl-11 pr-4 outline-none focus:border-amber-500"
          />
        </div>

        {/* Flight price alert */}
        {activeTab === "flights" && (
          <div className="mb-8 bg-slate-900 border border-slate-800 rounded-xl p-4">
            <label className="block text-sm text-slate-400 mb-2">
              Set flight price alert
            </label>

            <input
              type="number"
              placeholder="Notify me when flights are below this price"
              value={alertPrice}
              onChange={(event) => setAlertPrice(event.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg py-3 px-4 outline-none focus:border-amber-500"
            />

            <p className="text-xs text-slate-500 mt-2">
              Mock feature: alerts are checked against the current mock flight
              prices.
            </p>
          </div>
        )}

        {/* Hotel price alert */}
        {activeTab === "hotels" && (
          <div className="mb-8 bg-slate-900 border border-slate-800 rounded-xl p-4">
            <label className="block text-sm text-slate-400 mb-2">
              Set hotel price alert
            </label>

            <input
              type="number"
              placeholder="Notify me when hotels are below this price per night"
              value={hotelAlertPrice}
              onChange={(event) => setHotelAlertPrice(event.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg py-3 px-4 outline-none focus:border-amber-500"
            />

            <p className="text-xs text-slate-500 mt-2">
              Mock feature: alerts are checked against the current mock hotel
              prices.
            </p>
          </div>
        )}

        {/* Flights */}
        {activeTab === "flights" && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Available Flights</h2>

              <p className="text-sm text-slate-400">
                Sorted from lowest to highest price
              </p>
            </div>

            <div className="grid gap-4">
              {filteredFlights.map((flight) => {
                const isBelowTarget =
                  targetPrice > 0 && flight.price <= targetPrice;

                return (
                  <div
                    key={flight.id}
                    className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                  >
                    <div>
                      <h3 className="text-lg font-semibold">
                        {flight.city}, {flight.country}
                      </h3>

                      <p className="text-slate-400 text-sm">
                        {flight.route}
                      </p>

                      <p className="text-slate-400 text-sm mt-1">
                        {flight.airline} · {flight.duration} · {flight.stops}
                      </p>

                      {isBelowTarget && (
                        <p className="text-sm text-green-400 mt-3">
                          Price alert: This flight is within your budget!
                        </p>
                      )}
                    </div>

                    <div className="text-left md:text-right">
                      <p className="text-sm text-slate-400">from</p>

                      <p className="text-2xl font-bold text-amber-500">
                        ${flight.price}
                      </p>
                    </div>
                  </div>
                );
              })}

              {filteredFlights.length === 0 && (
                <p className="text-slate-400">No flights found.</p>
              )}
            </div>
          </section>
        )}

        {/* Hotels */}
        {activeTab === "hotels" && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Available Hotels</h2>

              <p className="text-sm text-slate-400">
                Sorted from lowest to highest price
              </p>
            </div>

            <div className="grid gap-4">
              {filteredHotels.map((hotel) => {
                const isBelowTarget =
                  hotelTargetPrice > 0 && hotel.price <= hotelTargetPrice;

                return (
                  <div
                    key={hotel.id}
                    className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
                  >
                    <div>
                      <h3 className="text-lg font-semibold">{hotel.name}</h3>

                      <p className="text-slate-400 text-sm">
                        {hotel.city}, {hotel.country}
                      </p>

                      <p className="text-slate-400 text-sm mt-1">
                        Rating: {hotel.rating}/10
                      </p>

                      {isBelowTarget && (
                        <p className="text-sm text-green-400 mt-3">
                          Price alert: This hotel is within your budget!
                        </p>
                      )}
                    </div>

                    <div className="text-left md:text-right">
                      <p className="text-sm text-slate-400">per night from</p>

                      <p className="text-2xl font-bold text-amber-500">
                        ${hotel.price}
                      </p>
                    </div>
                  </div>
                );
              })}

              {filteredHotels.length === 0 && (
                <p className="text-slate-400">No hotels found.</p>
              )}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default TravelPlanningPage;