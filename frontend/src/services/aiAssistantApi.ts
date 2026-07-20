export type AiAssistantRequest = {
  message: string;
};

export type AiAssistantResponse = {
  reply: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function sendMessageToAiAssistant(
  message: string,
): Promise<AiAssistantResponse> {
  const response = await fetch(`${API_BASE_URL}/assistant/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

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