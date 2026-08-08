import { getToken } from "./authApi";

export type TravelPreferences = {
  origin?: string;
  departure_date?: string;
  return_date?: string;
  check_in_date?: string;
  check_out_date?: string;
  travellers?: number;
};

export type AiAssistantRequest = {
  message: string;
  travel_preferences?: TravelPreferences;
};

export type AiAssistantResponse = {
  reply: string;
  intent: string;
  destinations_used: string[];
  missing_fields: string[];
  data_last_updated: string | null;
};

type FastApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type FastApiErrorBody = {
  detail?: string | FastApiValidationError[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function formatValidationError(
  errors: FastApiValidationError[],
): string {
  const messages = errors
    .map((error) => {
      const fieldPath = error.loc
        ?.filter((part) => part !== "body")
        .join(".");

      if (fieldPath && error.msg) {
        return `${fieldPath}: ${error.msg}`;
      }

      return error.msg;
    })
    .filter((message): message is string => Boolean(message));

  if (messages.length === 0) {
    return "Some of the submitted travel details are invalid.";
  }

  return messages.join(" ");
}

async function getAssistantErrorMessage(
  response: Response,
): Promise<string> {
  const errorBody = (
    await response.json().catch(() => null)
  ) as FastApiErrorBody | null;

  if (typeof errorBody?.detail === "string") {
    return errorBody.detail;
  }

  if (Array.isArray(errorBody?.detail)) {
    return formatValidationError(errorBody.detail);
  }

  if (response.status === 400) {
    return "The submitted travel details could not be processed.";
  }

  if (response.status === 401) {
    return "Your login session has expired. Please log in again.";
  }

  if (response.status === 422) {
    return "Some of the submitted travel details are invalid.";
  }

  if (response.status === 429) {
    return (
      "The AI assistant is receiving too many requests. " +
      "Please wait a moment and try again."
    );
  }

  if (response.status === 503) {
    return (
      "The TravelBuddiez AI assistant is temporarily unavailable. " +
      "Please try again shortly."
    );
  }

  return `The request failed with status ${response.status}.`;
}

export async function sendMessageToAiAssistant(
  request: AiAssistantRequest,
): Promise<AiAssistantResponse> {
  const token = getToken();

  if (token == null) {
    throw new Error("LOGIN_REQUIRED");
  }

  console.log(
    "Outgoing AI request:",
    JSON.stringify(request, null, 2),
  );

  const response = await fetch(`${API_BASE_URL}/assistant/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (response.status === 401) {
    throw new Error("LOGIN_REQUIRED");
  }

   if (!response.ok) {
    const errorMessage = await getAssistantErrorMessage(
      response,
    );

    console.error("AI assistant backend error:", {
      status: response.status,
      statusText: response.statusText,
      message: errorMessage,
    });

    if (response.status === 401) {
      throw new Error("LOGIN_REQUIRED");
    }

    throw new Error(errorMessage);
  }

  return response.json() as Promise<AiAssistantResponse>;
}

export async function saveAiResponse(data: {
    title?: string;
    user_message: string;
    ai_response: string;
}) {
    const token = getToken();

    if (!token) {
        throw new Error("LOGIN_REQUIRED");
    }

    const response = await fetch(
        `${API_BASE_URL}/assistant/saved-responses`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(data),
        },
    );

    if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
            errorData.detail ?? "Unable to save AI response.",
        );
    }

    return response.json();
}


export async function getSavedAiResponses() {
    const token = getToken();

    if (!token) {
        throw new Error("LOGIN_REQUIRED");
    }

    const response = await fetch(
        `${API_BASE_URL}/assistant/saved-responses`,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        },
    );

    if (!response.ok) {
        throw new Error(
            "Unable to load saved AI responses.",
        );
    }

    return response.json();
}


export async function deleteSavedAiResponse(
    responseId: number,
) {
    const token = getToken();

    if (!token) {
        throw new Error("LOGIN_REQUIRED");
    }

    const response = await fetch(
        `${API_BASE_URL}/assistant/saved-responses/${responseId}`,
        {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        },
    );

    if (!response.ok) {
        throw new Error(
            "Unable to delete saved AI response.",
        );
    }

    return response.json();
}