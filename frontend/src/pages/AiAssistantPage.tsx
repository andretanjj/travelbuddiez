// src/pages/AiAssistantPage.tsx

import { useState } from "react";
import type { SyntheticEvent } from "react";
import { HiOutlinePaperAirplane } from "react-icons/hi2";
import { sendMessageToAiAssistant } from "../services/aiAssistantApi";
import ReactMarkdown from "react-markdown";

type ChatMessage = {
    role: "user" | "assistant";
    content: string;
};

type AssistantResponse = {
    reply: string;
};

export default function AiAssistantPage() {
    const [destination, setDestination] = useState("");
    const [travelDates, setTravelDates] = useState("");
    const [interests, setInterests] = useState("");
    const [concerns, setConcerns] = useState("");
    const [question, setQuestion] = useState("");

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    function buildPrompt() {
        const promptParts = [
            destination && `Destination: ${destination}`,
            travelDates && `Travel dates: ${travelDates}`,
            interests && `Travel interests: ${interests}`,
            concerns && `Travel concerns: ${concerns}`,
            question && `Question: ${question}`,
        ];

        return promptParts.filter(Boolean).join("\n");
    }

    async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        const prompt = buildPrompt();

        if (!prompt.trim()) {
            setError("Please provide some travel information or enter a question.");
            return;
        }

        const userMessage: ChatMessage = {
            role: "user",
            content: prompt,
        };

        setMessages((currentMessages) => [
            ...currentMessages,
            userMessage,
        ]);

        setIsLoading(true);
        setError("");

        try {
            const data: AssistantResponse = await sendMessageToAiAssistant(prompt);

            setMessages((currentMessages) => [
                ...currentMessages,
                {
                    role: "assistant",
                    content: data.reply,
                },
            ]);

            setQuestion("");
        } catch (error) {
            console.error("Unable to connect to AI assistant:", error);

            setError(
                "The travel assistant is currently unavailable. Please try again.",
            );
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <main className="min-h-screen bg-slate-950 px-4 py-24 text-white">
            <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[380px_1fr]">
                <section className="rounded-2xl border border-white/10 bg-slate-900 p-6">
                    <div className="mb-6">
                        <p className="text-sm font-medium text-cyan-400">
                            TravelBuddiez AI
                        </p>

                        <h1 className="mt-2 text-3xl font-bold">
                            Ask your travel assistant
                        </h1>

                        <p className="mt-3 text-sm leading-6 text-slate-400">
                            Complete the template below to receive more relevant travel
                            advice.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <FormField
                            label="Destination"
                            placeholder="For example: Japan"
                            value={destination}
                            onChange={setDestination}
                        />

                        <FormField
                            label="Travel dates"
                            placeholder="For example: 10–17 December 2026"
                            value={travelDates}
                            onChange={setTravelDates}
                        />

                        <FormField
                            label="Interests"
                            placeholder="Food, nature, shopping, museums..."
                            value={interests}
                            onChange={setInterests}
                        />

                        <FormField
                            label="Travel concerns"
                            placeholder="Weather, safety, transport, health..."
                            value={concerns}
                            onChange={setConcerns}
                        />

                        <div>
                            <label
                                htmlFor="travel-question"
                                className="mb-2 block text-sm font-medium text-slate-200"
                            >
                                Your question
                            </label>

                            <textarea
                                id="travel-question"
                                rows={4}
                                value={question}
                                onChange={(event) => setQuestion(event.target.value)}
                                placeholder="What would you like to know?"
                                className="
                  w-full resize-none rounded-xl
                  border border-white/10 bg-slate-950
                  px-4 py-3 text-sm text-white
                  placeholder:text-slate-500
                  focus:border-cyan-400 focus:outline-none
                "
                            />
                        </div>

                        {error && (
                            <p className="text-sm text-red-400">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="
                flex w-full items-center justify-center gap-2
                rounded-xl bg-cyan-500 px-4 py-3
                font-semibold text-slate-950
                transition hover:bg-cyan-400
                disabled:cursor-not-allowed disabled:opacity-60
              "
                        >
                            <HiOutlinePaperAirplane className="h-5 w-5" />

                            {isLoading ? "Asking assistant..." : "Ask Travel AI"}
                        </button>
                    </form>
                </section>

                <ChatPanel messages={messages} isLoading={isLoading} />
            </div>
        </main>
    );
}

type FormFieldProps = {
    label: string;
    placeholder: string;
    value: string;
    onChange: (value: string) => void;
};

function FormField({
    label,
    placeholder,
    value,
    onChange,
}: FormFieldProps) {
    const inputId = label.toLowerCase().replaceAll(" ", "-");

    return (
        <div>
            <label
                htmlFor={inputId}
                className="mb-2 block text-sm font-medium text-slate-200"
            >
                {label}
            </label>

            <input
                id={inputId}
                type="text"
                value={value}
                onChange={(event) => onChange(event.target.value)}
                placeholder={placeholder}
                className="
          w-full rounded-xl
          border border-white/10 bg-slate-950
          px-4 py-3 text-sm text-white
          placeholder:text-slate-500
          focus:border-cyan-400 focus:outline-none
        "
            />
        </div>
    );
}

type ChatPanelProps = {
    messages: ChatMessage[];
    isLoading: boolean;
};

function ChatPanel({ messages, isLoading }: ChatPanelProps) {
    return (
        <section className="flex min-h-[650px] flex-col rounded-2xl border border-white/10 bg-slate-900">
            <div className="border-b border-white/10 px-6 py-5">
                <h2 className="font-semibold">Conversation</h2>

                <p className="mt-1 text-sm text-slate-400">
                    Travel-related questions only
                </p>
            </div>

            <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-6">
                {messages.length === 0 && (
                    <div className="m-auto max-w-md text-center">
                        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cyan-500/10 text-3xl">
                            ✈️
                        </div>

                        <h3 className="mt-5 text-xl font-semibold">
                            Plan your next journey
                        </h3>

                        <p className="mt-2 text-sm leading-6 text-slate-400">
                            Ask about destinations, travel advisories, weather, safety,
                            activities or itinerary planning.
                        </p>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div
                        key={`${message.role}-${index}`}
                        className={
                            message.role === "user"
                                ? "ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-cyan-500 px-4 py-3 text-sm text-slate-950"
                                : "mr-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-md bg-slate-800 px-4 py-3 text-sm leading-6 text-slate-100"
                        }
                    >
                        {message.role === "assistant" ? (
                            <ReactMarkdown
                                components={{
                                    h1: ({ children }) => (
                                        <h1 className="mb-2 text-lg font-semibold">{children}</h1>
                                    ),
                                    h2: ({ children }) => (
                                        <h2 className="mb-2 mt-3 text-base font-semibold">{children}</h2>
                                    ),
                                    h3: ({ children }) => (
                                        <h3 className="mb-1.5 mt-3 text-sm font-semibold text-cyan-300">
                                            {children}
                                        </h3>
                                    ),
                                    p: ({ children }) => (
                                        <p className="mb-2 leading-6 last:mb-0">{children}</p>
                                    ),
                                    ul: ({ children }) => (
                                        <ul className="mb-2 list-disc space-y-1 pl-5">{children}</ul>
                                    ),
                                    ol: ({ children }) => (
                                        <ol className="mb-2 list-decimal space-y-1 pl-5">{children}</ol>
                                    ),
                                    li: ({ children }) => (
                                        <li className="leading-6">{children}</li>
                                    ),
                                    strong: ({ children }) => (
                                        <strong className="font-semibold text-white">{children}</strong>
                                    ),
                                    hr: () => <hr className="my-3 border-white/10" />,
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        ) : (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                    </div>
                ))}

                {isLoading && (
                    <div className="mr-auto rounded-2xl rounded-bl-md bg-slate-800 px-4 py-3 text-sm text-slate-400">
                        The assistant is preparing a response...
                    </div>
                )}
            </div>
        </section>
    );
}