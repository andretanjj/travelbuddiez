import { useEffect, useState } from "react";
import { Bell, BellOff, Hotel, Plane, RefreshCw, Trash2} from "lucide-react";

import { useAuth } from "../context/AuthContext";

import {
  deleteSavedFlight,
  deleteSavedHotel,
  getSavedFlights,
  getSavedHotels,
  refreshSavedFlight,
  refreshSavedHotel,
} from "../services/savedTravelApi";

import {
  createFlightPriceAlert,
  createHotelPriceAlert,
  deactivatePriceAlert,
  getPriceAlerts,
} from "../services/priceAlertApi";

import type { PriceAlert } from "../types/priceAlert";

import type { SavedFlight, SavedHotel } from "../types/savedTravel";

import { getCurrencyRate } from "../services/travelApi";

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

const SUPPORTED_CURRENCIES = [
  "SGD",
  "USD",
  "EUR",
  "GBP",
  "JPY",
  "KRW",
  "MYR",
  "AUD",
] as const;

type SupportedCurrency = (typeof SUPPORTED_CURRENCIES)[number];

function SavedTravelPage() {
  const { user, isLoading: isAuthLoading } = useAuth();

  const [savedFlights, setSavedFlights] = useState<SavedFlight[]>([]);
  const [savedHotels, setSavedHotels] = useState<SavedHotel[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [refreshingItem, setRefreshingItem] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  // Stores all alerts belonging to the logged-in user.
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);

  // Stores the alert input for each saved item separately.
  // Example key: "flight-3" or "hotel-5".
  const [alertInputs, setAlertInputs] = useState<Record<string, string>>({});

  // Tracks which alert operation is currently running.
  const [updatingAlertItem, setUpdatingAlertItem] = useState<string | null>(null);

  // Tracks the saved item currently being deleted.
  const [deletingItem, setDeletingItem] = useState<string | null>(null);

  // Shared display-currency preference.
  // Uses the same localStorage key as TravelPlanningPage.
  const [displayCurrency, setDisplayCurrency] =
    useState<SupportedCurrency>(() => {
      const savedCurrency =
        localStorage.getItem("displayCurrency");

      if (
        savedCurrency &&
        SUPPORTED_CURRENCIES.includes(
          savedCurrency as SupportedCurrency
        )
      ) {
        return savedCurrency as SupportedCurrency;
      }

      return "SGD";
    });

  // Cache exchange rates such as USD-SGD.
  const [currencyRates, setCurrencyRates] = useState<Record<string, number>>({});

  function convertPrice(
    amount: number,
    sourceCurrency: string
  ): number {
    if (sourceCurrency === displayCurrency) {
      return amount;
    }

    const rateKey =
      `${sourceCurrency}-${displayCurrency}`;

    const rate = currencyRates[rateKey];

    // Keep original value temporarily while the rate loads.
    if (rate === undefined) {
      return amount;
    }

    return amount * rate;
  }

  useEffect(() => {
    // Remember the selected currency across pages and browser refreshes.
    localStorage.setItem(
      "displayCurrency",
      displayCurrency
    );
  }, [displayCurrency]);

  useEffect(() => {
    async function loadCurrencyRates() {
      // Collect all provider currencies currently stored
      // in the user's saved travel.
      const sourceCurrencies = new Set<string>([
        ...savedFlights.map(
          (flight) => flight.currency
        ),
        ...savedHotels.map(
          (hotel) => hotel.currency
        ),
      ]);

      for (const sourceCurrency of sourceCurrencies) {
        if (sourceCurrency === displayCurrency) {
          continue;
        }

        const rateKey =
          `${sourceCurrency}-${displayCurrency}`;

        if (currencyRates[rateKey] !== undefined) {
          continue;
        }

        try {
          const response = await getCurrencyRate(
            sourceCurrency,
            displayCurrency
          );

          setCurrencyRates((currentRates) => ({
            ...currentRates,
            [rateKey]: response.rate,
          }));
        } catch (error) {
          console.error(
            `Unable to convert ${sourceCurrency} to ${displayCurrency}:`,
            error
          );
        }
      }
    }

    loadCurrencyRates();
  }, [
    savedFlights,
    savedHotels,
    displayCurrency,
    currencyRates,
  ]);

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
        // Load saved travel and alerts concurrently.
        const [flightResponse, hotelResponse, alertResponse] = await Promise.all([
          getSavedFlights(),
          getSavedHotels(),
          getPriceAlerts(),
        ]);

        setSavedFlights(flightResponse.results);
        setSavedHotels(hotelResponse.results);
        setPriceAlerts(alertResponse.results);
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

  useEffect(() => {
    /*
      Automatically clears refresh/delete/alert feedback after 3 seconds.
    */

    if (!message) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setMessage("");
    }, 3000);

    // Prevent stale timers when another message appears quickly.
    return () => window.clearTimeout(timeoutId);
  }, [message]);


  function getFlightAlert(savedFlightId: number): PriceAlert | undefined {
    /*
      Finds the active alert linked to a saved flight.
    */

    return priceAlerts.find(
      (alert) =>
        alert.alert_type === "flight" &&
        alert.saved_flight_id === savedFlightId &&
        alert.is_active
    );
  }

  function getHotelAlert(savedHotelId: number): PriceAlert | undefined {
    /*
      Finds the active alert linked to a saved hotel.
    */

    return priceAlerts.find(
      (alert) =>
        alert.alert_type === "hotel" &&
        alert.saved_hotel_id === savedHotelId &&
        alert.is_active
    );
  }

  function updateAlertInput(itemKey: string, value: string) {
    /*
      Updates only the input belonging to the selected saved item.
    */

    setAlertInputs((currentInputs) => ({
      ...currentInputs,
      [itemKey]: value,
    }));
  }

  async function handleSetFlightAlert(
    savedFlightId: number,
  ) {
    /*
      Creates a new alert or updates the existing active alert.
      The backend handles duplicate prevention.
    */

    const itemKey = `flight-${savedFlightId}`;
    const targetPrice = Number(alertInputs[itemKey]);

    if (!Number.isFinite(targetPrice) || targetPrice <= 0) {
      setMessage("Enter a valid flight target price greater than zero.");
      return;
    }

    setUpdatingAlertItem(itemKey);
    setMessage("");

    try {
      const updatedAlert = await createFlightPriceAlert(
        savedFlightId,
        targetPrice,
        displayCurrency
      );

      setPriceAlerts((currentAlerts) => {
        const existingIndex = currentAlerts.findIndex(
          (alert) => alert.id === updatedAlert.id
        );

        // Replace an existing alert returned by the backend.
        if (existingIndex !== -1) {
          return currentAlerts.map((alert) =>
            alert.id === updatedAlert.id ? updatedAlert : alert
          );
        }

        // Add a newly created alert.
        return [updatedAlert, ...currentAlerts];
      });

      setAlertInputs((currentInputs) => ({
        ...currentInputs,
        [itemKey]: "",
      }));

      setMessage(
        `Flight price alert set for ${displayCurrency} ${targetPrice}.`
      );
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to set flight price alert.");
      }
    } finally {
      setUpdatingAlertItem(null);
    }
  }

  async function handleDeactivateFlightAlert(alert: PriceAlert) {
    const itemKey = `flight-${alert.saved_flight_id}`;

    setUpdatingAlertItem(itemKey);
    setMessage("");

    try {
      const deactivatedAlert = await deactivatePriceAlert(alert.id);

      // Keep the alert history, but replace it with its inactive version.
      setPriceAlerts((currentAlerts) =>
        currentAlerts.map((currentAlert) =>
          currentAlert.id === deactivatedAlert.id
            ? deactivatedAlert
            : currentAlert
        )
      );

      setMessage("Flight price alert deactivated.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to deactivate flight price alert.");
      }
    } finally {
      setUpdatingAlertItem(null);
    }
  }

  async function handleSetHotelAlert(
    savedHotelId: number
  ) {
    /*
      Creates a new hotel alert or updates its existing active alert.
    */

    const itemKey = `hotel-${savedHotelId}`;
    const targetPrice = Number(alertInputs[itemKey]);

    if (!Number.isFinite(targetPrice) || targetPrice <= 0) {
      setMessage("Enter a valid hotel target price greater than zero.");
      return;
    }

    setUpdatingAlertItem(itemKey);
    setMessage("");

    try {
      const updatedAlert = await createHotelPriceAlert(
        savedHotelId,
        targetPrice,
        displayCurrency,
      );

      setPriceAlerts((currentAlerts) => {
        const alertAlreadyExists = currentAlerts.some(
          (alert) => alert.id === updatedAlert.id
        );

        if (alertAlreadyExists) {
          return currentAlerts.map((alert) =>
            alert.id === updatedAlert.id ? updatedAlert : alert
          );
        }

        return [updatedAlert, ...currentAlerts];
      });

      setAlertInputs((currentInputs) => ({
        ...currentInputs,
        [itemKey]: "",
      }));

      setMessage(
        `Hotel price alert set for ${displayCurrency} ${targetPrice}.`
      );
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to set hotel price alert.");
      }
    } finally {
      setUpdatingAlertItem(null);
    }
  }

  async function handleDeactivateHotelAlert(alert: PriceAlert) {
    const itemKey = `hotel-${alert.saved_hotel_id}`;

    setUpdatingAlertItem(itemKey);
    setMessage("");

    try {
      const deactivatedAlert = await deactivatePriceAlert(alert.id);

      setPriceAlerts((currentAlerts) =>
        currentAlerts.map((currentAlert) =>
          currentAlert.id === deactivatedAlert.id
            ? deactivatedAlert
            : currentAlert
        )
      );

      setMessage("Hotel price alert deactivated.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to deactivate hotel price alert.");
      }
    } finally {
      setUpdatingAlertItem(null);
    }
  }

  async function handleDeleteFlight(savedFlightId: number) {
    /*
      Deletes the saved flight from PostgreSQL.

      After the backend confirms deletion, remove the item and any linked
      alert from local React state.
    */

    const itemKey = `flight-${savedFlightId}`;

    setDeletingItem(itemKey);
    setMessage("");

    try {
      await deleteSavedFlight(savedFlightId);

      // Remove the deleted flight without reloading the entire page.
      setSavedFlights((currentFlights) =>
        currentFlights.filter((flight) => flight.id !== savedFlightId)
      );

      // Remove any linked price alert from the current page state.
      setPriceAlerts((currentAlerts) =>
        currentAlerts.filter(
          (alert) => alert.saved_flight_id !== savedFlightId
        )
      );

      setMessage("Saved flight removed.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to remove saved flight.");
      }
    } finally {
      setDeletingItem(null);
    }
  }


  async function handleDeleteHotel(savedHotelId: number) {
    /*
      Deletes the saved hotel from PostgreSQL and updates the page state.
    */

    const itemKey = `hotel-${savedHotelId}`;

    setDeletingItem(itemKey);
    setMessage("");

    try {
      await deleteSavedHotel(savedHotelId);

      setSavedHotels((currentHotels) =>
        currentHotels.filter((hotel) => hotel.id !== savedHotelId)
      );

      setPriceAlerts((currentAlerts) =>
        currentAlerts.filter(
          (alert) => alert.saved_hotel_id !== savedHotelId
        )
      );

      setMessage("Saved hotel removed.");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Unable to remove saved hotel.");
      }
    } finally {
      setDeletingItem(null);
    }
  }

  async function handleRefreshFlight(savedFlightId: number) {
    /*
      Refreshes one saved flight price and updates it in the page state.
    */

    setRefreshingItem(`flight-${savedFlightId}`);
    setMessage("");

    try {
      const updatedFlight = await refreshSavedFlight(savedFlightId);

      // Reload alerts because the backend may have changed pending to triggered.
      const alertResponse = await getPriceAlerts();
      setPriceAlerts(alertResponse.results);

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

      // Reload the latest alert statuses after evaluating the new hotel price.
      const alertResponse = await getPriceAlerts();
      setPriceAlerts(alertResponse.results);

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

        {/* Display currency selector */}
        <div className="mb-6 flex items-center justify-end gap-3">
          <label className="text-sm text-slate-400">
            Display currency
          </label>

          <select
            value={displayCurrency}
            onChange={(event) =>
              setDisplayCurrency(
                event.target.value as SupportedCurrency
              )
            }
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-amber-500"
          >
            {SUPPORTED_CURRENCIES.map((currency) => (
              <option key={currency} value={currency}>
                {currency}
              </option>
            ))}
          </select>
        </div>

        <section className="mb-10">
          <div className="mb-4 flex items-center gap-2">
            <Plane className="h-5 w-5 text-amber-400" />
            <h2 className="text-xl font-semibold">Saved Flights</h2>
          </div>

          <div className="grid gap-4">
            {savedFlights.map((flight) => {
              const activeAlert = getFlightAlert(flight.id);
              const itemKey = `flight-${flight.id}`;

              return (
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

                  {flight.return_date && (
                    <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Return journey
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {flight.destination_code} → {flight.origin_code}
                      </p>

                      {flight.return_flight_number && (
                        <p className="mt-1 text-xs text-slate-500">
                          Flight: {flight.return_flight_number}
                        </p>
                      )}
                    </div>
                  )}

                  {flight.return_date ? (
                    <>
                      <p className="mt-2 inline-flex rounded-full border border-blue-400/30 bg-blue-400/10 px-2 py-1 text-xs font-medium text-blue-300">
                        Round trip
                      </p>

                      <p className="mt-2 text-sm text-slate-500">
                        Outbound: {flight.departure_date}
                      </p>

                      <p className="mt-1 text-sm text-slate-500">
                        Return: {flight.return_date}
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="mt-2 inline-flex rounded-full border border-slate-600 bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300">
                        One way
                      </p>

                      <p className="mt-2 text-sm text-slate-500">
                        Departure: {flight.departure_date}
                      </p>
                    </>
                  )}

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
                    {displayCurrency}{" "}
                    {convertPrice(
                      Number(flight.saved_price),
                      flight.currency
                    ).toFixed(2)}
                  </p>

                  {flight.current_price !== null && (
                    <>
                      <p className="mt-2 text-sm text-slate-400">
                        current price
                      </p>

                      <p className="text-lg font-semibold text-white">
                        {displayCurrency}{" "}
                        {convertPrice(
                          Number(flight.current_price),
                          flight.currency
                        ).toFixed(2)}
                      </p>
                    </>
                  )}

                  <div className="mt-4 border-t border-slate-800 pt-4">
                    {activeAlert ? (
                      <>
                        <div className="flex items-center gap-2 md:justify-end">
                          <Bell size={15} className="text-green-400" />

                          <p className="text-sm text-green-400">
                            Alert: {activeAlert.target_currency} {activeAlert.target_price}
                          </p>
                        </div>

                        <p className="mt-1 text-xs text-slate-500">
                          Status: {activeAlert.notification_status}
                        </p>

                        <button
                          type="button"
                          onClick={() => handleDeactivateFlightAlert(activeAlert)}
                          disabled={updatingAlertItem === itemKey}
                          className="mt-3 inline-flex items-center gap-2 rounded-lg border border-red-400/50 px-3 py-2 text-sm text-red-300 transition hover:bg-red-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <BellOff size={14} />
                          {updatingAlertItem === itemKey
                            ? "Updating..."
                            : "Deactivate alert"}
                        </button>
                      </>
                    ) : (
                      <>
                        <label className="block text-sm text-slate-400">
                          Price alert target
                        </label>

                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          value={alertInputs[itemKey] ?? ""}
                          onChange={(event) =>
                            updateAlertInput(itemKey, event.target.value)
                          }
                          placeholder={`Target in ${displayCurrency}`}
                          className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-amber-500 md:w-48"
                        />

                        <p className="mt-1 text-xs text-slate-500">
                          Alert will be checked and emailed in {displayCurrency}.
                        </p>

                        <button
                          type="button"
                          onClick={() =>
                            handleSetFlightAlert(flight.id)
                          }
                          disabled={updatingAlertItem === itemKey}
                          className="mt-2 inline-flex items-center gap-2 rounded-lg border border-green-500 px-3 py-2 text-sm font-semibold text-green-400 transition hover:bg-green-500 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <Bell size={14} />
                          {updatingAlertItem === itemKey
                            ? "Setting..."
                            : "Set alert"}
                        </button>
                      </>
                    )}
                  </div>

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

                  <button
                    type="button"
                    onClick={() => handleDeleteFlight(flight.id)}
                    disabled={deletingItem === itemKey}
                    className="ml-2 mt-3 inline-flex items-center gap-2 rounded-lg border border-red-400/50 px-4 py-2 text-sm font-semibold text-red-300 transition hover:bg-red-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 size={14} />

                    {deletingItem === itemKey ? "Removing..." : "Remove"}
                  </button>
                </div>
              </div>
            );
          })}

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
            {savedHotels.map((hotel) => {
              const activeAlert = getHotelAlert(hotel.id);
              const itemKey = `hotel-${hotel.id}`;

              return (
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
                    {displayCurrency}{" "}
                    {convertPrice(
                      Number(hotel.saved_price),
                      hotel.currency
                    ).toFixed(2)}
                  </p>

                  {hotel.current_price !== null && (
                    <>
                      <p className="mt-2 text-sm text-slate-400">
                        current total
                      </p>

                      <p className="text-lg font-semibold text-white">
                        {displayCurrency}{" "}
                        {convertPrice(
                          Number(hotel.current_price),
                          hotel.currency
                        ).toFixed(2)}
                      </p>
                    </>
                  )}

                  {/* Price-alert controls for this saved hotel. */}
                  <div className="mt-4 border-t border-slate-800 pt-4">
                    {activeAlert ? (
                      <>
                        <div className="flex items-center gap-2 md:justify-end">
                          <Bell size={15} className="text-green-400" />

                          <p className="text-sm text-green-400">
                            Alert: {activeAlert.target_currency} {activeAlert.target_price}
                          </p>
                        </div>

                        <p className="mt-1 text-xs text-slate-500">
                          Status: {activeAlert.notification_status}
                        </p>

                        <button
                          type="button"
                          onClick={() => handleDeactivateHotelAlert(activeAlert)}
                          disabled={updatingAlertItem === itemKey}
                          className="mt-3 inline-flex items-center gap-2 rounded-lg border border-red-400/50 px-3 py-2 text-sm text-red-300 transition hover:bg-red-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <BellOff size={14} />

                          {updatingAlertItem === itemKey
                            ? "Updating..."
                            : "Deactivate alert"}
                        </button>
                      </>
                    ) : (
                      <>
                        <label className="block text-sm text-slate-400">
                          Price alert target
                        </label>

                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          value={alertInputs[itemKey] ?? ""}
                          onChange={(event) =>
                            updateAlertInput(itemKey, event.target.value)
                          }
                          placeholder={`Target in ${displayCurrency}`}
                          className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-amber-500 md:w-48"
                        />

                        <p className="mt-1 text-xs text-slate-500">
                          Alert will be checked and emailed in {displayCurrency}.
                        </p>

                        <button
                          type="button"
                          onClick={() =>
                            handleSetHotelAlert(hotel.id)
                          }
                          disabled={updatingAlertItem === itemKey}
                          className="mt-2 inline-flex items-center gap-2 rounded-lg border border-green-500 px-3 py-2 text-sm font-semibold text-green-400 transition hover:bg-green-500 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <Bell size={14} />

                          {updatingAlertItem === itemKey
                            ? "Setting..."
                            : "Set alert"}
                        </button>
                      </>
                    )}
                  </div>

                  {/* Manually refresh the latest hotel price. */}
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

                  <button
                    type="button"
                    onClick={() => handleDeleteHotel(hotel.id)}
                    disabled={deletingItem === itemKey}
                    className="ml-2 mt-3 inline-flex items-center gap-2 rounded-lg border border-red-400/50 px-4 py-2 text-sm font-semibold text-red-300 transition hover:bg-red-400/10 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 size={14} />

                    {deletingItem === itemKey ? "Removing..." : "Remove"}
                  </button>
                </div>
              </div>
            );
          })}

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