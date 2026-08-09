interface UnsplashPhoto {
  id: string;
  alt_description: string | null;
  urls: {
    regular: string;
  };
  user: {
    name: string;
    links: {
      html: string;
    };
  };
  links: {
    html: string;
    download_location: string;
  };
}

interface UnsplashSearchResponse {
  total: number;
  total_pages: number;
  results: UnsplashPhoto[];
}

export interface DestinationImage {
  imageUrl: string;
  altDescription: string;
  photographerName: string;
  photographerUrl: string;
  unsplashUrl: string;
  downloadLocation: string;
}


const UNSPLASH_API_BASE_URL = "https://api.unsplash.com";


function getUnsplashAccessKey(): string {
  // Vite exposes frontend environment variables that begin with VITE_.
  const accessKey = import.meta.env.VITE_UNSPLASH_ACCESS_KEY;

  if (!accessKey) {
    throw new Error("VITE_UNSPLASH_ACCESS_KEY is not configured.");
  }

  return accessKey;
}


export async function getDestinationImage(searchQuery: string): Promise<DestinationImage | null> {
  const accessKey = getUnsplashAccessKey();

  // Unsplash's official Search Photos endpoint supports query,
  // orientation, content_filter, order_by, and per_page.
  const queryParams = new URLSearchParams({
    query: searchQuery,
    orientation: "landscape",
    content_filter: "high",
    order_by: "relevant",
    per_page: "1",
  });

  const response = await fetch(`${UNSPLASH_API_BASE_URL}/search/photos?${queryParams.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Client-ID ${accessKey}`,
      "Accept-Version": "v1",
    },
  });

  if (!response.ok) {
    throw new Error(`Unable to search Unsplash images: ${response.status}`);
  }

  const data: UnsplashSearchResponse = await response.json();
  const photo = data.results[0];

  if (!photo) {
    return null;
  }

  /*
    Keep the original Unsplash URL and its ixid parameter.

    Width and height parameters request a reasonably sized landscape image
    instead of embedding the original multi-megabyte photograph in the PDF.
  */
  const imageUrl = new URL(photo.urls.regular);
  imageUrl.searchParams.set("w", "1600");
  imageUrl.searchParams.set("h", "500");
  imageUrl.searchParams.set("fit", "crop");

  return {
    imageUrl: imageUrl.toString(),
    altDescription: photo.alt_description ?? searchQuery,
    photographerName: photo.user.name,
    photographerUrl: photo.user.links.html,
    unsplashUrl: photo.links.html,
    downloadLocation: photo.links.download_location,
  };
}


export async function triggerUnsplashDownload(downloadLocation: string): Promise<void> {
  const accessKey = getUnsplashAccessKey();

  /*
    Unsplash requires applications to call the photo's download-location
    endpoint when the photo is used in a download-like action.

    Exporting the image into the user's PDF is such an action.
  */
  const response = await fetch(downloadLocation, {
    method: "GET",
    headers: {
      Authorization: `Client-ID ${accessKey}`,
      "Accept-Version": "v1",
    },
  });

  if (!response.ok) {
    console.warn(`Unable to register Unsplash download: ${response.status}`);
  }
}