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
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
    const errorBody = await response.text();

    console.error("AI assistant backend error:", {
      status: response.status,
      statusText: response.statusText,
      body: errorBody,
    });

    throw new Error(
      `AI assistant request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<AiAssistantResponse>;
}