import { jsPDF } from "jspdf";

import { getDestinationImage, triggerUnsplashDownload } from "./destinationImageApi";

import type { DestinationImage } from "./destinationImageApi";
import type { PriceAlert } from "../types/priceAlert";
import type { SavedFlight, SavedHotel } from "../types/savedTravel";


interface GenerateTripPlanPdfParams {
  flights: SavedFlight[];
  hotels: SavedHotel[];
  priceAlerts: PriceAlert[];
  displayCurrency: string;
  convertPrice: (amount: number, sourceCurrency: string) => number;
}


function formatDate(dateValue: string | null | undefined): string {
  if (!dateValue) {
    return "Not available";
  }

  const date = new Date(`${dateValue}T00:00:00`);

  return date.toLocaleDateString("en-SG", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}


function formatPrice(amount: number): string {
  return amount.toFixed(2);
}


function formatDuration(duration: string | null | undefined): string {
  if (!duration) {
    return "Not available";
  }

  // Duffel commonly returns ISO 8601 durations such as PT18H30M.
  const match = duration.match(/^PT(?:(\d+)H)?(?:(\d+)M)?$/);

  if (!match) {
    return duration;
  }

  const hours = match[1] ? Number(match[1]) : 0;
  const minutes = match[2] ? Number(match[2]) : 0;

  if (hours > 0 && minutes > 0) {
    return `${hours}h ${minutes}m`;
  }

  if (hours > 0) {
    return `${hours}h`;
  }

  if (minutes > 0) {
    return `${minutes}m`;
  }

  return duration;
}


function formatCountry(country: string): string {
  if (!country) {
    return "Not available";
  }

  // Hotel providers may return ISO country codes such as "de".
  if (country.length === 2) {
    try {
      const regionNames = new Intl.DisplayNames(["en"], { type: "region" });
      return regionNames.of(country.toUpperCase()) ?? country.toUpperCase();
    } catch {
      return country.toUpperCase();
    }
  }

  return country;
}


function getFlightAlert(priceAlerts: PriceAlert[], savedFlightId: number): PriceAlert | undefined {
  return priceAlerts.find((alert) => alert.alert_type === "flight" && alert.saved_flight_id === savedFlightId && alert.is_active);
}


function getHotelAlert(priceAlerts: PriceAlert[], savedHotelId: number): PriceAlert | undefined {
  return priceAlerts.find((alert) => alert.alert_type === "hotel" && alert.saved_hotel_id === savedHotelId && alert.is_active);
}


function getDestinationSearchQuery(flights: SavedFlight[], hotels: SavedHotel[]): string {
  /*
    Prefer the selected flight destination because that usually represents
    the main destination of the exported trip.

    If no flight is selected, use the first selected hotel's city/country.
  */

  if (flights.length > 0) {
    const destination = flights[0].destination_name;

    // A selected hotel can give us extra country context for better search results.
    if (hotels.length > 0) {
      return `${destination} ${formatCountry(hotels[0].country)} travel city`;
    }

    return `${destination} travel city`;
  }

  if (hotels.length > 0) {
    return `${hotels[0].city} ${formatCountry(hotels[0].country)} travel city`;
  }

  return "travel destination";
}


async function convertImageToJpegDataUrl(imageUrl: string): Promise<string> {
  /*
    Fetch the image through the Unsplash CDN first.

    We then draw it to a canvas and export JPEG. This gives jsPDF a
    predictable image format and keeps the PDF image reasonably compressed.
  */
  const response = await fetch(imageUrl);

  if (!response.ok) {
    throw new Error(`Unable to load destination image: ${response.status}`);
  }

  const imageBlob = await response.blob();
  const imageObjectUrl = URL.createObjectURL(imageBlob);

  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const imageElement = new Image();

      imageElement.onload = () => resolve(imageElement);
      imageElement.onerror = () => reject(new Error("Unable to decode destination image."));
      imageElement.src = imageObjectUrl;
    });

    /*
      The PDF uses a wide hero image.

      The canvas crops the source photo to a fixed wide aspect ratio instead
      of stretching the source and distorting the photograph.
    */
    const canvasWidth = 1600;
    const canvasHeight = 500;
    const targetAspectRatio = canvasWidth / canvasHeight;
    const sourceAspectRatio = image.width / image.height;

    let sourceX = 0;
    let sourceY = 0;
    let sourceWidth = image.width;
    let sourceHeight = image.height;

    if (sourceAspectRatio > targetAspectRatio) {
      sourceWidth = image.height * targetAspectRatio;
      sourceX = (image.width - sourceWidth) / 2;
    } else {
      sourceHeight = image.width / targetAspectRatio;
      sourceY = (image.height - sourceHeight) / 2;
    }

    const canvas = document.createElement("canvas");
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    const context = canvas.getContext("2d");

    if (!context) {
      throw new Error("Unable to prepare the destination image.");
    }

    context.drawImage(image, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, canvasWidth, canvasHeight);

    // JPEG gives a much smaller PDF than storing the full original image.
    return canvas.toDataURL("image/jpeg", 0.82);
  } finally {
    URL.revokeObjectURL(imageObjectUrl);
  }
}


export async function generateTripPlanPdf({ flights, hotels, priceAlerts, displayCurrency, convertPrice }: GenerateTripPlanPdfParams): Promise<void> {
  if (flights.length === 0 && hotels.length === 0) {
    throw new Error("Select at least one saved flight or hotel.");
  }

  /*
    Destination imagery is optional.

    A temporary image-service failure should not prevent users from
    exporting their saved travel details.
  */
  let destinationImage: DestinationImage | null = null;
  let destinationImageDataUrl: string | null = null;

  try {
    const searchQuery = getDestinationSearchQuery(flights, hotels);
    destinationImage = await getDestinationImage(searchQuery);

    if (destinationImage) {
      destinationImageDataUrl = await convertImageToJpegDataUrl(destinationImage.imageUrl);
    }
  } catch (error) {
    console.error("Unable to add destination image to Trip Plan:", error);
  }

  // jsPDF creates an A4 portrait document by default.
  const doc = new jsPDF();

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  const margin = 16;
  const contentWidth = pageWidth - margin * 2;
  const footerReservedHeight = 22;

  let y = 14;


  function addPage(): void {
    doc.addPage();
    y = 18;

    // Small TravelBuddiez label on continuation pages.
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(8, 145, 178);
    doc.text("TravelBuddiez", margin, y);

    doc.setTextColor(30, 41, 59);
    y += 10;
  }


  function checkPageSpace(requiredHeight: number): void {
    // Keep enough room for the final disclaimer/footer.
    if (y + requiredHeight > pageHeight - footerReservedHeight) {
      addPage();
    }
  }


  function addSectionTitle(title: string): void {
    checkPageSpace(13);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.setTextColor(15, 23, 42);
    doc.text(title, margin, y);

    y += 3;

    doc.setDrawColor(203, 213, 225);
    doc.setLineWidth(0.3);
    doc.line(margin, y, pageWidth - margin, y);

    y += 6;
  }


  function addJourneyCard(title: string, route: string, dateLabel: string, date: string, flightNumber: string | null, airline?: string, stops?: string, duration?: string): void {
    const hasExtraDetails = Boolean(airline || stops || duration);
    const cardHeight = hasExtraDetails ? 29 : 22;

    checkPageSpace(cardHeight + 3);

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(margin, y, contentWidth, cardHeight, 2, 2, "FD");

    const cardTop = y;

    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(8, 145, 178);
    doc.text(title.toUpperCase(), margin + 5, cardTop + 6);

    doc.setFontSize(11);
    doc.setTextColor(15, 23, 42);
    doc.text(route, margin + 5, cardTop + 12);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(71, 85, 105);
    doc.text(`${dateLabel}: ${date}`, margin + 5, cardTop + 18);

    if (flightNumber) {
      doc.text(`Flight: ${flightNumber}`, margin + 75, cardTop + 18);
    }

    if (hasExtraDetails) {
      // Use simple ASCII separators because jsPDF's default Helvetica
      // does not reliably render every Unicode symbol.
      const details = [airline, stops, duration ? formatDuration(duration) : null].filter(Boolean).join("  |  ");
      doc.text(details, margin + 5, cardTop + 24);
    }

    y += cardHeight + 5;
  }


  /*
    Destination hero image.
  */

  if (destinationImage && destinationImageDataUrl) {
    const imageHeight = 50;

    // jsPDF's documented addImage API accepts a base64 data URL.
    doc.addImage(destinationImageDataUrl, "JPEG", margin, y, contentWidth, imageHeight, undefined, "FAST");

    y += imageHeight + 3;

    // Unsplash requires attribution for API-provided photographs.
    doc.setFont("helvetica", "italic");
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);
    doc.text(`Photo by ${destinationImage.photographerName} on Unsplash`, margin, y);

    y += 6;
  }


  /*
    Header.
  */

  doc.setFillColor(8, 145, 178);
  doc.roundedRect(margin, y, contentWidth, 27, 3, 3, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(255, 255, 255);
  doc.text("TravelBuddiez", margin + 7, y + 10);

  doc.setFontSize(14);
  doc.text("Trip Plan", margin + 7, y + 18);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text("Your selected travel details in one place", margin + 7, y + 23);

  y += 35;


  /*
    Trip overview.
  */

  const primaryFlight = flights[0];

  if (primaryFlight) {
    addSectionTitle("Trip Overview");

    const overviewHeight = primaryFlight.return_date ? 29 : 24;

    checkPageSpace(overviewHeight + 5);

    doc.setFillColor(241, 245, 249);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(margin, y, contentWidth, overviewHeight, 3, 3, "FD");

    const overviewY = y;

    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(15, 23, 42);
    doc.text(`${primaryFlight.origin_name}  ---  ${primaryFlight.destination_name}`, margin + 6, overviewY + 8);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(71, 85, 105);
    doc.text(primaryFlight.return_date ? "Round trip" : "One way", margin + 6, overviewY + 15);
    doc.text(`Departure: ${formatDate(primaryFlight.departure_date)}`, margin + 45, overviewY + 15);

    if (primaryFlight.return_date) {
      doc.text(`Return: ${formatDate(primaryFlight.return_date)}`, margin + 45, overviewY + 21);
    }

    y += overviewHeight + 7;
  }


  /*
    Flights.
  */

  if (flights.length > 0) {
    addSectionTitle("Flights");

    flights.forEach((flight, index) => {
      checkPageSpace(flight.return_date ? 78 : 48);

      if (flights.length > 1) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.setTextColor(15, 23, 42);
        doc.text(`Flight ${index + 1}`, margin, y);

        y += 6;
      }

      addJourneyCard("Outbound", `${flight.origin_code}  ---  ${flight.destination_code}`, "Departure", formatDate(flight.departure_date), flight.flight_number, flight.airline, flight.stops, flight.duration);

      if (flight.return_date) {
        addJourneyCard("Return", `${flight.destination_code}  ---  ${flight.origin_code}`, "Departure", formatDate(flight.return_date), flight.return_flight_number);
      }

      const currentPrice = Number(flight.current_price ?? flight.saved_price);
      const convertedCurrentPrice = convertPrice(currentPrice, flight.currency);
      const activeAlert = getFlightAlert(priceAlerts, flight.id);

      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(71, 85, 105);
      doc.text("Current price", margin, y);

      doc.setFontSize(11);
      doc.setTextColor(15, 23, 42);
      doc.text(`${displayCurrency} ${formatPrice(convertedCurrentPrice)}`, margin + 37, y);

      if (activeAlert) {
        doc.setFontSize(8.5);
        doc.setFont("helvetica", "normal");
        doc.setTextColor(22, 163, 74);
        doc.text(`Price alert: ${activeAlert.target_currency} ${formatPrice(Number(activeAlert.target_price))}`, margin + 95, y);
      }

      y += 8;
    });
  }


  /*
    Accommodation.
  */

  if (hotels.length > 0) {
    addSectionTitle("Accommodation");

    hotels.forEach((hotel, index) => {
      const cardHeight = 36;

      checkPageSpace(cardHeight + 8);

      doc.setFillColor(248, 250, 252);
      doc.setDrawColor(226, 232, 240);
      doc.roundedRect(margin, y, contentWidth, cardHeight, 2, 2, "FD");

      const cardY = y;

      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(15, 23, 42);
      doc.text(hotels.length > 1 ? `Hotel ${index + 1}: ${hotel.hotel_name}` : hotel.hotel_name, margin + 5, cardY + 7);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(8.5);
      doc.setTextColor(71, 85, 105);
      doc.text(`${hotel.city}, ${formatCountry(hotel.country)}`, margin + 5, cardY + 13);

      doc.text(`Check-in: ${formatDate(hotel.check_in_date)}`, margin + 5, cardY + 19);
      doc.text(`Check-out: ${formatDate(hotel.check_out_date)}`, margin + 75, cardY + 19);

      if (hotel.rating > 0) {
        doc.text(`Rating: ${hotel.rating}/10`, margin + 5, cardY + 25);
      }

      const currentPrice = Number(hotel.current_price ?? hotel.saved_price);
      const convertedCurrentPrice = convertPrice(currentPrice, hotel.currency);

      doc.setFont("helvetica", "bold");
      doc.setTextColor(15, 23, 42);
      doc.text(`Current price: ${displayCurrency} ${formatPrice(convertedCurrentPrice)}`, margin + 75, cardY + 25);

      const activeAlert = getHotelAlert(priceAlerts, hotel.id);

      if (activeAlert) {
        doc.setFont("helvetica", "normal");
        doc.setTextColor(22, 163, 74);
        doc.text(`Price alert: ${activeAlert.target_currency} ${formatPrice(Number(activeAlert.target_price))}`, margin + 5, cardY + 31);
      }

      y += cardHeight + 6;
    });
  }


  /*
    Price summary.
  */

  checkPageSpace(43);
  addSectionTitle("Price Summary");

  const flightTotal = flights.reduce((total, flight) => {
    const price = Number(flight.current_price ?? flight.saved_price);
    return total + convertPrice(price, flight.currency);
  }, 0);

  const hotelTotal = hotels.reduce((total, hotel) => {
    const price = Number(hotel.current_price ?? hotel.saved_price);
    return total + convertPrice(price, hotel.currency);
  }, 0);

  const estimatedTotal = flightTotal + hotelTotal;
  const summaryHeight = 31;

  doc.setFillColor(240, 253, 250);
  doc.setDrawColor(153, 246, 228);
  doc.roundedRect(margin, y, contentWidth, summaryHeight, 3, 3, "FD");

  const summaryY = y;

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(71, 85, 105);

  doc.text("Flights", margin + 6, summaryY + 8);
  doc.text(`${displayCurrency} ${formatPrice(flightTotal)}`, pageWidth - margin - 6, summaryY + 8, { align: "right" });

  doc.text("Accommodation", margin + 6, summaryY + 14);
  doc.text(`${displayCurrency} ${formatPrice(hotelTotal)}`, pageWidth - margin - 6, summaryY + 14, { align: "right" });

  doc.setDrawColor(153, 246, 228);
  doc.line(margin + 6, summaryY + 19, pageWidth - margin - 6, summaryY + 19);

  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(15, 23, 42);

  doc.text("Estimated total", margin + 6, summaryY + 27);
  doc.text(`${displayCurrency} ${formatPrice(estimatedTotal)}`, pageWidth - margin - 6, summaryY + 27, { align: "right" });

  y += summaryHeight + 7;


  /*
    Disclaimer and footer.
  */

  const disclaimer = "Prices and availability may change. Refresh your saved travel items and verify important information with the relevant provider before booking.";
  const disclaimerLines = doc.splitTextToSize(disclaimer, contentWidth);
  const footerStartY = pageHeight - 18;

  if (y > footerStartY - 12) {
    addPage();
  }

  const finalFooterY = Math.max(y + 5, pageHeight - 18);

  doc.setDrawColor(226, 232, 240);
  doc.line(margin, finalFooterY - 5, pageWidth - margin, finalFooterY - 5);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.text(disclaimerLines, margin, finalFooterY);

  doc.setFont("helvetica", "italic");
  doc.setFontSize(7);
  doc.text(`Generated by TravelBuddiez on ${new Date().toLocaleDateString("en-SG")}`, margin, pageHeight - 7);


  /*
    Register the image use with Unsplash.

    Do this only after the image has successfully been included in the
    document. A failure here should not prevent the PDF from being saved.
  */

  if (destinationImage && destinationImageDataUrl) {
    try {
      await triggerUnsplashDownload(destinationImage.downloadLocation);
    } catch (error) {
      console.warn("Unable to register Unsplash photo download:", error);
    }
  }


  /*
    Build a safe filename using the selected destination.
  */

  const destinationName = flights[0]?.destination_name ?? hotels[0]?.destination_name ?? "trip";
  const safeDestinationName = destinationName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  doc.save(`travelbuddiez-${safeDestinationName}-trip-plan.pdf`);
}