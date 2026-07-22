import { useEffect, useState } from "react";
import { Hotel, Plane, RefreshCw } from "lucide-react";

import { useAuth } from "../context/AuthContext";

import {
  getSavedFlights,
  getSavedHotels,
  refreshSavedFlight,
  refreshSavedHotel,
} from "../services/savedTravelApi";

import type { SavedFlight, SavedHotel } from "../types/savedTravel";

function getPriceStatusLabel(priceStatus: string): string {
  //Converts backend price status into user-friendly text.

  if (priceStatus === "price_dropped") {
    return "Price dropped";
  }

  if (priceStatus === "price_increased") {
    return "Price increased";
  }

  if (priceStatus === "unchanged") {
    return "Unchanged";
  }

  if (priceStatus === "unavailable") {
    return "Unavailable";
  }

  return "Saved snapshot";
}

function SavedTravelPage() {
  const { user, isLoading: isAuthLoading } = useAuth();

  const [savedFlights, setSavedFlights] = useState<SavedFlight[]>([]);
  const [savedHotels, setSavedHotels] = useState<SavedHotel[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [refreshingItem, setRefreshingItem] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadSavedTravel() {
      /*
        Only logged-in users can view saved travel.
        If user is not logged in, skip the API calls.
      */

      if (user === null) {
        return;
      }

      setIsLoading(true);
      setMessage("");

      try {
        const [flightResponse, hotelResponse] = await Promise.all([
          getSavedFlights(),
          getSavedHotels(),
        ]);

        setSavedFlights(flightResponse.results);
        setSavedHotels(hotelResponse.results);
      } catch (error) {
        if (error instanceof Error) {
          setMessage(error.message);
        } else {
          setMessage("Unable to load saved travel.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    if (!isAuthLoading) {
      loadSavedTravel();
    }
  }, [user, isAuthLoading]);

  async function handleRefreshFlight(savedFlightId: number) {
    /*
      Refreshes one saved flight price and updates it in the page state.
    */

    setRefreshingItem(`flight-${savedFlightId}`);
    setMessage("");

    try {
      const updatedFlight = await refreshSavedFlight(savedFlightId);

      setSavedFlights((currentFlights) =>
        currentFlights.map((flight) =>
          flight.id === updatedFlight.id ? updatedFlight : flight
        )
      );

      setMessage("Flight price refreshed.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to refresh flight price.");
      }
    } finally {
      setRefreshingItem(null);
    }
  }

  async function handleRefreshHotel(savedHotelId: number) {
    /*
      Refreshes one saved hotel price and updates it in the page state.
    */

    setRefreshingItem(`hotel-${savedHotelId}`);
    setMessage("");

    try {
      const updatedHotel = await refreshSavedHotel(savedHotelId);

      setSavedHotels((currentHotels) =>
        currentHotels.map((hotel) =>
          hotel.id === updatedHotel.id ? updatedHotel : hotel
        )
      );

      setMessage("Hotel price refreshed.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to refresh hotel price.");
      }
    } finally {
      setRefreshingItem(null);
    }
  }

  if (isAuthLoading) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
        <div className="mx-auto max-w-5xl">
          <p className="text-slate-400">Checking login status...</p>
        </div>
      </main>
    );
  }

  if (user === null) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
        <div className="mx-auto max-w-5xl rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h1 className="text-2xl font-bold">Saved Travel</h1>

          <p className="mt-3 text-slate-400">
            Please log in to view your saved flights and hotels.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-2 text-3xl font-bold">Saved Travel</h1>

        <p className="mb-8 text-slate-400">
          View saved flight and hotel snapshots. Refresh prices before booking
          because saved prices may become outdated.
        </p>

        {message && (
          <div className="mb-6 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
            {message}
          </div>
        )}

        {isLoading && (
          <p className="mb-6 text-slate-400">Loading saved travel...</p>
        )}

        <section className="mb-10">
          <div className="mb-4 flex items-center gap-2">
            <Plane className="h-5 w-5 text-amber-400" />
            <h2 className="text-xl font-semibold">Saved Flights</h2>
          </div>

          <div className="grid gap-4">
            {savedFlights.map((flight) => (
              <div
                key={flight.id}
                className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <h3 className="text-lg font-semibold">
                    {flight.origin_name} → {flight.destination_name}
                  </h3>

                  <p className="text-sm text-slate-400">
                    {flight.origin_code} → {flight.destination_code}
                  </p>

                  <p className="mt-1 text-sm text-slate-400">
                    {flight.airline} · {flight.duration} · {flight.stops}
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    Departure: {flight.departure_date}
                  </p>

                  <p className="mt-2 text-sm text-slate-400">
                    Status: {getPriceStatusLabel(flight.price_status)}
                  </p>

                  {flight.last_checked_at && (
                    <p className="mt-1 text-xs text-slate-500">
                      Last checked: {new Date(flight.last_checked_at).toLocaleString()}
                    </p>
                  )}
                </div>

                <div className="text-left md:text-right">
                  <p className="text-sm text-slate-400">saved price</p>

                  <p className="text-xl font-bold text-amber-500">
                    {flight.currency} {flight.saved_price}
                  </p>

                  {flight.current_price !== null && (
                    <>
                      <p className="mt-2 text-sm text-slate-400">
                        current price
                      </p>

                      <p className="text-lg font-semibold text-white">
                        {flight.currency} {flight.current_price}
                      </p>
                    </>
                  )}

                  <button
                    type="button"
                    onClick={() => handleRefreshFlight(flight.id)}
                    disabled={refreshingItem === `flight-${flight.id}`}
                    className="mt-3 inline-flex items-center gap-2 rounded-lg border border-amber-500 px-4 py-2 text-sm font-semibold text-amber-400 transition hover:bg-amber-500 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <RefreshCw size={14} />
                    {refreshingItem === `flight-${flight.id}`
                      ? "Refreshing..."
                      : "Refresh price"}
                  </button>
                </div>
              </div>
            ))}

            {!isLoading && savedFlights.length === 0 && (
              <p className="text-slate-400">No saved flights yet.</p>
            )}
          </div>
        </section>

        <section>
          <div className="mb-4 flex items-center gap-2">
            <Hotel className="h-5 w-5 text-amber-400" />
            <h2 className="text-xl font-semibold">Saved Hotels</h2>
          </div>

          <div className="grid gap-4">
            {savedHotels.map((hotel) => (
              <div
                key={hotel.id}
                className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-5 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <h3 className="text-lg font-semibold">{hotel.hotel_name}</h3>

                  <p className="text-sm text-slate-400">
                    {hotel.city}, {hotel.country}
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    {hotel.check_in_date} → {hotel.check_out_date}
                  </p>

                  {hotel.rating > 0 && (
                    <p className="mt-1 text-sm text-slate-400">
                      Rating: {hotel.rating}/10
                    </p>
                  )}

                  <p className="mt-2 text-sm text-slate-400">
                    Status: {getPriceStatusLabel(hotel.price_status)}
                  </p>

                  {hotel.last_checked_at && (
                    <p className="mt-1 text-xs text-slate-500">
                      Last checked: {new Date(hotel.last_checked_at).toLocaleString()}
                    </p>
                  )}
                </div>

                <div className="text-left md:text-right">
                  <p className="text-sm text-slate-400">saved total</p>

                  <p className="text-xl font-bold text-amber-500">
                    {hotel.currency} {hotel.saved_price}
                  </p>

                  {hotel.current_price !== null && (
                    <>
                      <p className="mt-2 text-sm text-slate-400">
                        current total
                      </p>

                      <p className="text-lg font-semibold text-white">
                        {hotel.currency} {hotel.current_price}
                      </p>
                    </>
                  )}

                  <button
                    type="button"
                    onClick={() => handleRefreshHotel(hotel.id)}
                    disabled={refreshingItem === `hotel-${hotel.id}`}
                    className="mt-3 inline-flex items-center gap-2 rounded-lg border border-amber-500 px-4 py-2 text-sm font-semibold text-amber-400 transition hover:bg-amber-500 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <RefreshCw size={14} />
                    {refreshingItem === `hotel-${hotel.id}`
                      ? "Refreshing..."
                      : "Refresh price"}
                  </button>
                </div>
              </div>
            ))}

            {!isLoading && savedHotels.length === 0 && (
              <p className="text-slate-400">No saved hotels yet.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

export default SavedTravelPage;