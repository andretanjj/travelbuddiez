import { useEffect, useRef, useState } from "react";
import { Plane, Hotel, Search, MapPin } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import type { SavedFlight, SavedHotel } from "../types/savedTravel";
import {
  deleteSavedFlight,
  deleteSavedHotel,
  getSavedFlights,
  getSavedHotels,
  saveFlight,
  saveHotel,
} from "../services/savedTravelApi";

import {
  searchFlights,
  searchHotels,
  searchTravelPlaces,
} from "../services/travelApi";

import {
  createFlightPriceAlert,
  createHotelPriceAlert,
} from "../services/priceAlertApi";

import type {
  ActiveTravelTab,
  FlightResult,
  HotelResult,
  TravelPlaceSuggestion,
} from "../types/travel";

type SuggestionTarget = "origin" | "destination" | "hotel";

function TravelPlanningPage() {
  const [activeTab, setActiveTab] = useState<ActiveTravelTab>("flights");

  // Flight search form states.
  // Input text is what the user sees.
  // Selected code is what we send to Duffel.
  const [originInput, setOriginInput] = useState("");
  const [destinationInput, setDestinationInput] = useState("");
  const [selectedOriginCode, setSelectedOriginCode] = useState("");
  const [selectedDestinationCode, setSelectedDestinationCode] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  // Users can search either one-way or round-trip flights.
  const [tripType, setTripType] = useState<"one-way" | "round-trip">("round-trip");
  // Only required for round-trip searches.
  const [returnDate, setReturnDate] = useState("");

  // Hotel search form states.
  // Input text is what the user sees.
  // Selected code is what we send to LiteAPI.
  const [hotelDestinationInput, setHotelDestinationInput] = useState("");
  const [selectedHotelCode, setSelectedHotelCode] = useState("");
  const [checkInDate, setCheckInDate] = useState("");
  const [checkOutDate, setCheckOutDate] = useState("");

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

  // Autocomplete states.
  const [suggestions, setSuggestions] = useState<TravelPlaceSuggestion[]>([]);
  const [activeSuggestionTarget, setActiveSuggestionTarget] =
    useState<SuggestionTarget | null>(null);
  const [isSuggestionLoading, setIsSuggestionLoading] = useState(false);

  // Used to avoid searching when the user just selected an option.
  const justSelectedSuggestionRef = useRef(false);

  const targetPrice = Number(alertPrice);
  const hotelTargetPrice = Number(hotelAlertPrice);

  // Used for saved travels
  const { user } = useAuth();
  const [saveMessage, setSaveMessage] = useState("");
  const [savingItemId, setSavingItemId] = useState<string | null>(null);

  // Saved database records belonging to the logged-in user.
  // These let the search cards show whether a result is already saved.
  const [savedFlights, setSavedFlights] = useState<SavedFlight[]>([]);
  const [savedHotels, setSavedHotels] = useState<SavedHotel[]>([]);

  const activeSearchText =
    activeSuggestionTarget === "origin"
      ? originInput
      : activeSuggestionTarget === "destination"
        ? destinationInput
        : activeSuggestionTarget === "hotel"
          ? hotelDestinationInput
          : "";

  useEffect(() => {
    // Do not search if no input is active.
    if (activeSuggestionTarget === null) {
      setSuggestions([]);
      return;
    }

    // Do not immediately search again after selecting a suggestion.
    if (justSelectedSuggestionRef.current) {
      justSelectedSuggestionRef.current = false;
      return;
    }

    const cleanedSearchText = activeSearchText.trim();

    // Backend requires at least 2 characters.
    if (cleanedSearchText.length < 2) {
      setSuggestions([]);
      return;
    }

    // Debounce: wait briefly after the user stops typing before calling backend.
    const timeoutId = window.setTimeout(async () => {
      try {
        setIsSuggestionLoading(true);

        const suggestionMode = activeSuggestionTarget === "hotel" ? "hotel" : "flight";

        const response = await searchTravelPlaces(
          cleanedSearchText,
          suggestionMode
        );

        setSuggestions(response.results);
      } catch (error) {
        console.error("Failed to load travel place suggestions:", error);
        setSuggestions([]);
      } finally {
        setIsSuggestionLoading(false);
      }
    }, 300);

    return () => window.clearTimeout(timeoutId);
  }, [activeSearchText, activeSuggestionTarget]);

  useEffect(() => {
    async function loadSavedTravel() {
      /*
        Guests may search, but only logged-in users have saved travel.

        Loading both saved lists allows the search result buttons to show
        "Flight saved" or "Hotel saved" for existing database records.
      */

      if (user === null) {
        setSavedFlights([]);
        setSavedHotels([]);
        return;
      }

      try {
        const [flightResponse, hotelResponse] = await Promise.all([
          getSavedFlights(),
          getSavedHotels(),
        ]);

        setSavedFlights(flightResponse.results);
        setSavedHotels(hotelResponse.results);
      } catch (error) {
        console.error("Unable to load saved travel state:", error);
      }
    }

    loadSavedTravel();
  }, [user]);

  useEffect(() => {
    /*
      Automatically clears save/remove/alert feedback after 3 seconds.
      Nothing happens when there is no message.
    */

    if (!saveMessage) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setSaveMessage("");
    }, 3000);

    // Clear the old timer if the message changes or the component unmounts.
    return () => window.clearTimeout(timeoutId);
  }, [saveMessage]);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    // Prevent browser refresh when the form is submitted.
    event.preventDefault();

    setIsLoading(true);
    setErrorMessage("");
    setSuggestions([]);
    setActiveSuggestionTarget(null);

    try {
      if (activeTab === "flights") {
        if (!selectedOriginCode || !selectedDestinationCode) {
          setErrorMessage("Please choose both flight locations from the dropdown suggestions.");
          return;
        }

        if (!departureDate) {
          setErrorMessage("Please choose a departure date.");
          return;
        }

        if (tripType === "round-trip") {
          if (!returnDate) {
            setErrorMessage("Please choose a return date.");
            return;
          }

          if (returnDate <= departureDate) {
            setErrorMessage("Return date must be after the departure date.");
            return;
          }
        }

        const flightResponse = await searchFlights({
          origin: selectedOriginCode,
          destination: selectedDestinationCode,
          departureDate,

          // One-way flights send no return date.
          returnDate:
            tripType === "round-trip"
              ? returnDate
              : undefined,

          adults,
        });

        setFlights(flightResponse.results);
      } else {
        if (!selectedHotelCode) {
          setErrorMessage("Please choose a hotel destination from the dropdown suggestions.");
          return;
        }

        if (!checkInDate || !checkOutDate) {
          setErrorMessage("Please choose both check-in and check-out dates.");
          return;
        }

        if (checkOutDate <= checkInDate) {
          setErrorMessage("Check-out date must be after check-in date.");
          return;
        }

        const hotelResponse = await searchHotels({
          city: selectedHotelCode,
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

  function handleSuggestionSelect(suggestion: TravelPlaceSuggestion) {
    /*
      The user should see the readable place name.
      The backend should receive the hidden travel code.

      Example:
      User sees: Bugis
      App sends: SIN
    */

    const displayValue = suggestion.name;
    const hiddenCode = suggestion.code || suggestion.name;

    justSelectedSuggestionRef.current = true;

    if (activeSuggestionTarget === "origin") {
      setOriginInput(displayValue);
      setSelectedOriginCode(hiddenCode);
    }

    if (activeSuggestionTarget === "destination") {
      setDestinationInput(displayValue);
      setSelectedDestinationCode(hiddenCode);
    }

    if (activeSuggestionTarget === "hotel") {
      setHotelDestinationInput(displayValue);
      setSelectedHotelCode(hiddenCode);
    }

    setSuggestions([]);
    setActiveSuggestionTarget(null);
  }

  function findSavedFlight(flight: FlightResult): SavedFlight | undefined {
    return savedFlights.find(
      (savedFlight) =>
        savedFlight.origin_code === selectedOriginCode &&
        savedFlight.destination_code === selectedDestinationCode &&
        savedFlight.departure_date === flight.departureDate &&

        // Distinguish one-way and round-trip snapshots.
        (savedFlight.return_date ?? null) ===
          (flight.returnDate ?? null) &&

        savedFlight.airline === flight.airline &&
        Number(savedFlight.saved_price) === Number(flight.price)
    );
  }


  function findSavedHotel(hotel: HotelResult): SavedHotel | undefined {
    /*
      Match the LiteAPI hotel snapshot using hotel name, destination,
      dates, and saved total price.
    */

    return savedHotels.find(
      (savedHotel) =>
        savedHotel.hotel_name === hotel.name &&
        savedHotel.destination_code === selectedHotelCode &&
        savedHotel.check_in_date === hotel.checkInDate &&
        savedHotel.check_out_date === hotel.checkOutDate &&
        Number(savedHotel.saved_price) === Number(hotel.price)
    );
  }

  async function handleToggleFlight(flight: FlightResult) {
    /*
      If the result is already saved, remove it.
      Otherwise, create a saved-flight row and optionally create its alert.
    */

    if (user === null) {
      setSaveMessage("Please log in to save this flight.");
      return;
    }

    const existingSavedFlight = findSavedFlight(flight);
    const itemKey = `flight-${flight.id}`;

    setSaveMessage("");
    setSavingItemId(itemKey);

    try {
      if (existingSavedFlight) {
        // Remove the saved row from PostgreSQL.
        await deleteSavedFlight(existingSavedFlight.id);

        // Keep frontend state synchronized with the database.
        setSavedFlights((currentFlights) =>
          currentFlights.filter(
            (savedFlight) => savedFlight.id !== existingSavedFlight.id
          )
        );

        setSaveMessage("Flight removed from Saved Travel.");
        return;
      }

      if (alertPrice !== "" && targetPrice <= 0) {
        setSaveMessage("Flight alert price must be greater than zero.");
        return;
      }

     const savedFlight = await saveFlight({
        provider_item_id: flight.providerItemId,
        origin_code: selectedOriginCode,
        origin_name: originInput,
        destination_code: selectedDestinationCode,
        destination_name: destinationInput,
        departure_date: flight.departureDate,
        return_date: flight.returnDate,
        price: flight.price,
        currency: flight.currency,
        airline: flight.airline,
        flight_number: flight.flightNumber,
        departure_at: flight.departureAt,
        duration: flight.duration,
        stops: flight.stops,
        provider: "duffel",
    });

      // Add the returned database record immediately.
      setSavedFlights((currentFlights) => [
        savedFlight,
        ...currentFlights,
      ]);

      if (targetPrice > 0) {
        await createFlightPriceAlert(savedFlight.id, targetPrice);

        setSaveMessage(
          `Flight saved. Price alert set for ${flight.currency} ${targetPrice}.`
        );
      } else {
        setSaveMessage("Flight saved successfully.");
      }
    } catch (error) {
      if (error instanceof Error) {
        setSaveMessage(error.message);
      } else {
        setSaveMessage("Unable to update saved flight.");
      }
    } finally {
      setSavingItemId(null);
    }
  }
  
 async function handleToggleHotel(hotel: HotelResult) {
    /*
      Toggles the selected hotel between saved and unsaved.
    */

    if (user === null) {
      setSaveMessage("Please log in to save this hotel.");
      return;
    }

    const existingSavedHotel = findSavedHotel(hotel);
    const itemKey = `hotel-${hotel.id}`;

    setSaveMessage("");
    setSavingItemId(itemKey);

    try {
      if (existingSavedHotel) {
        await deleteSavedHotel(existingSavedHotel.id);

        setSavedHotels((currentHotels) =>
          currentHotels.filter(
            (savedHotel) => savedHotel.id !== existingSavedHotel.id
          )
        );

        setSaveMessage("Hotel removed from Saved Travel.");
        return;
      }

      if (hotelAlertPrice !== "" && hotelTargetPrice <= 0) {
        setSaveMessage("Hotel alert price must be greater than zero.");
        return;
      }

      const savedHotel = await saveHotel({
        provider_item_id: hotel.id,
        destination_code: selectedHotelCode,
        destination_name: hotelDestinationInput,
        hotel_name: hotel.name,
        city: hotel.city,
        country: hotel.country,
        rating: hotel.rating,
        price: hotel.price,
        currency: hotel.currency,
        check_in_date: hotel.checkInDate,
        check_out_date: hotel.checkOutDate,
        provider: "liteapi",
      });

      setSavedHotels((currentHotels) => [
        savedHotel,
        ...currentHotels,
      ]);

      if (hotelTargetPrice > 0) {
        await createHotelPriceAlert(
          savedHotel.id,
          hotelTargetPrice
        );

        setSaveMessage(
          `Hotel saved. Price alert set for ${hotel.currency} ${hotelTargetPrice}.`
        );
      } else {
        setSaveMessage("Hotel saved successfully.");
      }
    } catch (error) {
      if (error instanceof Error) {
        setSaveMessage(error.message);
      } else {
        setSaveMessage("Unable to update saved hotel.");
      }
    } finally {
      setSavingItemId(null);
    }
  }

  function renderSuggestions(target: SuggestionTarget) {
    if (activeSuggestionTarget !== target) {
      return null;
    }

    if (suggestions.length === 0 && !isSuggestionLoading) {
      return null;
    }

    return (
      <div className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-xl border border-slate-700 bg-slate-950 shadow-2xl">
        {isSuggestionLoading && (
          <div className="px-4 py-3 text-sm text-slate-400">
            Searching places...
          </div>
        )}

        {!isSuggestionLoading &&
          suggestions.map((suggestion) => (
            <button
              key={`${suggestion.provider}-${suggestion.id}`}
              type="button"
              onMouseDown={() => handleSuggestionSelect(suggestion)}
              className="flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-slate-800"
            >
              <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />

              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-white">
                  {suggestion.name}
                </span>

                <span className="block truncate text-xs text-slate-400">
                  {suggestion.subtitle || suggestion.country || suggestion.city}
                  {suggestion.code ? ` · ${suggestion.code}` : ""}
                  {suggestion.type ? ` · ${suggestion.type}` : ""}
                </span>
              </span>
            </button>
          ))}
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-2 text-3xl font-bold">Travel Planning</h1>

        <p className="text-slate-400">
          Search and compare available flights and hotels.
        </p>

        <p className="mb-8 mt-2 text-xs text-slate-500">
          Flight results are powered by Duffel. Hotel availability and prices
          are powered by LiteAPI / Nuitee.
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
              {/* Flight trip type */}
              <div className="mb-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setTripType("round-trip");
                  }}
                  className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                    tripType === "round-trip"
                      ? "border-amber-500 bg-amber-500 text-slate-950"
                      : "border-slate-700 bg-slate-950 text-slate-300"
                  }`}
                >
                  Round trip
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setTripType("one-way");

                    // A one-way search must not accidentally send an old return date.
                    setReturnDate("");
                  }}
                  className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                    tripType === "one-way"
                      ? "border-amber-500 bg-amber-500 text-slate-950"
                      : "border-slate-700 bg-slate-950 text-slate-300"
                  }`}
                >
                  One way
                </button>
              </div>

              <div
                className={`grid gap-4 ${tripType === "round-trip" ? "md:grid-cols-5" : "md:grid-cols-4"}`}
              >
                <div className="relative">
                  <label className="mb-2 block text-sm text-slate-400">
                    From
                  </label>

                  <input
                    type="text"
                    value={originInput}
                    onFocus={() => setActiveSuggestionTarget("origin")}
                    onChange={(event) => {
                      setOriginInput(event.target.value);

                      // User changed the text manually, so previous selected code is no longer trusted.
                      setSelectedOriginCode("");

                      setActiveSuggestionTarget("origin");
                    }}
                    required
                    placeholder="Leaving from"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />

                  {renderSuggestions("origin")}
                </div>

                <div className="relative">
                  <label className="mb-2 block text-sm text-slate-400">
                    To
                  </label>

                  <input
                    type="text"
                    value={destinationInput}
                    onFocus={() => setActiveSuggestionTarget("destination")}
                    onChange={(event) => {
                      setDestinationInput(event.target.value);
                      setSelectedDestinationCode("");
                      setActiveSuggestionTarget("destination");
                    }}
                    required
                    placeholder="Going to"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />

                  {renderSuggestions("destination")}
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

                {tripType === "round-trip" && (
                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Return date
                  </label>

                  <input
                    type="date"
                    value={returnDate}
                    min={departureDate || undefined}
                    onChange={(event) => setReturnDate(event.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />
                </div>
)}

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
                Start typing a destination, then choose a suggestion. The app
                uses the selected travel code for live flight search.
              </p>
            </>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <div className="relative">
                  <label className="mb-2 block text-sm text-slate-400">
                    Hotel destination
                  </label>

                  <input
                    type="text"
                    value={hotelDestinationInput}
                    onFocus={() => setActiveSuggestionTarget("hotel")}
                    onChange={(event) => {
                      setHotelDestinationInput(event.target.value);
                      setSelectedHotelCode("");
                      setActiveSuggestionTarget("hotel");
                    }}
                    required
                    placeholder="Where to?"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                  />

                  {renderSuggestions("hotel")}
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
                Start typing a city, airport, or area, then choose a suggestion.
                Hotel names and ratings are enriched from LiteAPI / Nuitee.
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

        {saveMessage && (
          <div className="mb-6 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
            {saveMessage}
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
              Enter a target price before saving a flight to create a persistent
              price alert.
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
              placeholder="Notify me when hotels are below this total stay price"
              value={hotelAlertPrice}
              onChange={(event) => setHotelAlertPrice(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
            />

            <p className="mt-2 text-xs text-slate-500">
              Enter a target total stay price before saving a hotel to create a
              persistent price alert.
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
                const savedFlight = findSavedFlight(flight);
                const isSaved = savedFlight !== undefined;
                const itemKey = `flight-${flight.id}`;
                const isBelowTarget = targetPrice > 0 && flight.price <= targetPrice;

                return (
                  <div
                    key={flight.id}
                    className={`flex flex-col gap-4 rounded-2xl border p-5 transition md:flex-row md:items-center md:justify-between ${
                      isSaved
                        ? "border-green-500/60 bg-green-500/10"
                        : "border-slate-800 bg-slate-900"
                    }`}
                  >
                    <div>
                      <h3 className="text-lg font-semibold">
                        {flight.city}, {flight.country}
                      </h3>

                      {/* Outbound journey */}
                      <div className="mt-2">
                        <p className="text-sm font-medium text-slate-300">
                          Outbound
                        </p>

                        <p className="text-sm text-slate-400">
                          {flight.route}
                        </p>

                        <p className="mt-1 text-sm text-slate-400">
                          {flight.airline} · {flight.duration} · {flight.stops}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          Departure: {flight.departureDate}
                        </p>
                      </div>

                      {/* Only show this section when Duffel returned a return slice. */}
                      {flight.returnRoute && (
                        <div className="mt-4">
                          <p className="text-sm font-medium text-slate-300">
                            Return
                          </p>

                          <p className="text-sm text-slate-400">
                            {flight.returnRoute}
                          </p>

                          <p className="mt-1 text-sm text-slate-400">
                            {flight.returnDuration} · {flight.returnStops}
                          </p>

                          <p className="mt-1 text-sm text-slate-500">
                            Departure: {flight.returnDate}
                          </p>
                        </div>
                      )}

                      {isBelowTarget && (
                        <p className="mt-3 text-sm text-green-400">
                          Price alert: This flight is within your budget!
                        </p>
                      )}
                    </div>

                    <div className="text-left md:text-right">
                      <p className="text-sm text-slate-400">
                        {flight.returnDate ? "round-trip total" : "total"}
                      </p>

                      <p className="text-2xl font-bold text-amber-500">
                        {flight.currency} {flight.price}
                      </p>

                      <button
                        type="button"
                        onClick={() => handleToggleFlight(flight)}
                        disabled={savingItemId === itemKey}
                        className={`mt-3 rounded-lg border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                          isSaved
                            ? "border-green-500 bg-green-500 text-slate-950 hover:bg-green-400"
                            : "border-amber-500 text-amber-400 hover:bg-amber-500 hover:text-slate-950"
                        }`}
                      >
                        {savingItemId === itemKey
                          ? isSaved
                            ? "Removing..."
                            : "Saving..."
                          : isSaved
                            ? "Flight saved"
                            : "Save flight"}
                      </button>
                    </div>
                  </div>
                );
              })}

              {!isLoading && flights.length === 0 && (
                <p className="text-slate-400">
                  No flights found.
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
                const savedHotel = findSavedHotel(hotel);
                const isSaved = savedHotel !== undefined;
                const itemKey = `hotel-${hotel.id}`;
                const isBelowTarget = hotelTargetPrice > 0 && hotel.price <= hotelTargetPrice;

                return (
                  <div
                    key={hotel.id}
                    className={`flex flex-col gap-4 rounded-2xl border p-5 transition md:flex-row md:items-center md:justify-between ${
                    isSaved
                      ? "border-green-500/60 bg-green-500/10"
                      : "border-slate-800 bg-slate-900"
                  }`}
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
                      <p className="text-sm text-slate-400">total for stay</p>

                      <p className="text-2xl font-bold text-amber-500">
                        {hotel.currency} {hotel.price}
                      </p>

                      <button
                        type="button"
                        onClick={() => handleToggleHotel(hotel)}
                        disabled={savingItemId === itemKey}
                        className={`mt-3 rounded-lg border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                          isSaved
                            ? "border-green-500 bg-green-500 text-slate-950 hover:bg-green-400"
                            : "border-amber-500 text-amber-400 hover:bg-amber-500 hover:text-slate-950"
                        }`}
                      >
                        {savingItemId === itemKey
                          ? isSaved
                            ? "Removing..."
                            : "Saving..."
                          : isSaved
                            ? "Hotel saved"
                            : "Save hotel"}
                      </button>
                    </div>
                  </div>
                );
              })}

              {!isLoading && hotels.length === 0 && (
                <p className="text-slate-400">
                  No hotels found.
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