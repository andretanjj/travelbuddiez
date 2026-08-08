import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
    HiOutlinePaperAirplane,
    HiOutlineBookmark,
    HiBookmark,
} from "react-icons/hi2";
import ReactMarkdown from "react-markdown";

import {
    sendMessageToAiAssistant,
    saveAiResponse,
    getSavedAiResponses,
    deleteSavedAiResponse,
} from "../services/aiAssistantApi";
import { getToken } from "../services/authApi";


type ChatMessage = {
    role: "user" | "assistant";
    content: string;
    userPrompt?: string;
    saved?: boolean;
};

type AssistantResponse = {
    reply: string;
};

type SavedAiResponse = {
    id: number;
    title: string | null;
    user_message: string;
    ai_response: string;
    saved_at: string;
};

export default function AiAssistantPage() {
    const navigate = useNavigate();
    const token = getToken();

    const [destination, setDestination] = useState("");
    const [origin, setOrigin] = useState("SIN");
    const [departureDate, setDepartureDate] = useState("");
    const [returnDate, setReturnDate] = useState("");
    const [travellers, setTravellers] = useState(1);

    const [interests, setInterests] = useState("");
    const [concerns, setConcerns] = useState("");
    const [question, setQuestion] = useState("");

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const [showSavedResponses, setShowSavedResponses] =
        useState(false);

    const [savedResponses, setSavedResponses] =
        useState<SavedAiResponse[]>([]);

    const travelPreferences = {
        ...(origin.trim()
            ? { origin: origin.trim().toUpperCase() }
            : {}),

        ...(departureDate
            ? { departure_date: departureDate }
            : {}),

        ...(returnDate
            ? {
                return_date: returnDate,
                check_out_date: returnDate,
            }
            : {}),

        ...(departureDate
            ? { check_in_date: departureDate }
            : {}),

        travellers,
    };


    function buildPrompt(): string {
        const promptParts = [
            destination
            && `Destination: ${destination.trim()}`,

            origin
            && `Departure airport: ${origin.trim().toUpperCase()}`,

            departureDate
            && `Departure date: ${departureDate}`,

            returnDate
            && `Return date: ${returnDate}`,

            `Travellers: ${travellers}`,

            interests
            && `Travel interests: ${interests.trim()}`,

            concerns
            && `Travel concerns: ${concerns.trim()}`,

            question
            && `Question: ${question.trim()}`,
        ];

        return promptParts
            .filter(Boolean)
            .join("\n");
    }

    async function handleSaveResponse(
        message: ChatMessage,
        index: number,
    ) {
        if (
            message.role !== "assistant"
            || !message.userPrompt
        ) {
            return;
        }

        try {
            const questionLine = message.userPrompt
                .split("\n")
                .find((line) =>
                    line.startsWith("Question:")
                );

            const title = questionLine
                ? questionLine
                    .replace("Question:", "")
                    .trim()
                : "Saved travel response";

            const savedResponse = await saveAiResponse({
                title,
                user_message: message.userPrompt,
                ai_response: message.content,
            });

            setSavedResponses((currentResponses) => [
                savedResponse,
                ...currentResponses,
            ]);

            setMessages((currentMessages) =>
                currentMessages.map(
                    (currentMessage, currentIndex) =>
                        currentIndex === index
                            ? {
                                ...currentMessage,
                                saved: true,
                            }
                            : currentMessage,
                )
            );
        } catch (caughtError) {
            console.error(
                "Unable to save AI response:",
                caughtError,
            );

            if (
                caughtError instanceof Error
                && caughtError.message === "LOGIN_REQUIRED"
            ) {
                navigate("/login");
                return;
            }

            setError(
                caughtError instanceof Error
                    ? caughtError.message
                    : "Unable to save AI response.",
            );
        }
    }

    async function handleOpenSavedResponses() {
        try {
            const data = await getSavedAiResponses();

            setSavedResponses(data);
            setShowSavedResponses(true);
        } catch (caughtError) {
            console.error(
                "Unable to load saved AI responses:",
                caughtError,
            );

            if (
                caughtError instanceof Error
                && caughtError.message === "LOGIN_REQUIRED"
            ) {
                navigate("/login");
                return;
            }

            setError(
                caughtError instanceof Error
                    ? caughtError.message
                    : "Unable to load saved responses.",
            );
        }
    }

    async function handleSubmit(
        event: SyntheticEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        if (!getToken()) {
            navigate("/login");
            return;
        }

        const prompt = buildPrompt();

        if (!prompt.trim()) {
            setError(
                "Please provide some travel information or enter a question.",
            );
            return;
        }

        if (
            departureDate
            && returnDate
            && returnDate <= departureDate
        ) {
            setError(
                "The return date must be after the departure date.",
            );
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
            const data: AssistantResponse =
                await sendMessageToAiAssistant({
                    message: prompt,
                    travel_preferences: travelPreferences,
                });

            setMessages((currentMessages) => [
                ...currentMessages,
                {
                    role: "assistant",
                    content: data.reply,
                    userPrompt: prompt,
                    saved: false,
                },
            ]);

            setQuestion("");
        } catch (caughtError) {
            console.error(
                "Unable to connect to AI assistant:",
                caughtError,
            );

            if (
                caughtError instanceof Error
                && caughtError.message === "LOGIN_REQUIRED"
            ) {
                navigate("/login");
                return;
            }

            if (caughtError instanceof Error) {
                setError(caughtError.message);
                return;
            }

            setError(
                "The travel assistant is currently unavailable. Please try again.",
            );
        } finally {
            setIsLoading(false);
        }
    }


    if (!token) {
        return (
            <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
                <section className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cyan-500/10 text-3xl">
                        🔒
                    </div>

                    <h1 className="mt-5 text-2xl font-bold">
                        Login required
                    </h1>

                    <p className="mt-3 text-sm leading-6 text-slate-400">
                        Please log in or register to use the
                        TravelBuddiez AI assistant.
                    </p>

                    <button
                        type="button"
                        onClick={() => navigate("/login")}
                        className="mt-6 w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400"
                    >
                        Log in
                    </button>

                    <button
                        type="button"
                        onClick={() => navigate("/register")}
                        className="mt-3 w-full rounded-xl border border-white/10 px-4 py-3 font-semibold text-white transition hover:bg-white/5"
                    >
                        Create account
                    </button>
                </section>
            </main>
        );
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
                            Complete the trip details below so the assistant
                            can retrieve relevant destination, flight and
                            hotel information.
                        </p>
                    </div>

                    <form
                        onSubmit={handleSubmit}
                        className="space-y-5"
                    >
                        <FormField
                            label="Destination"
                            placeholder="For example: Japan"
                            value={destination}
                            onChange={setDestination}
                        />

                        <FormField
                            label="Departure airport"
                            placeholder="For example: SIN"
                            value={origin}
                            onChange={(value) => {
                                setOrigin(
                                    value
                                        .toUpperCase()
                                        .slice(0, 3),
                                );
                            }}
                            maxLength={3}
                        />

                        <DateField
                            label="Departure date"
                            value={departureDate}
                            onChange={setDepartureDate}
                        />

                        <DateField
                            label="Return / check-out date"
                            value={returnDate}
                            onChange={setReturnDate}
                            min={departureDate || undefined}
                        />

                        <div>
                            <label
                                htmlFor="travellers"
                                className="mb-2 block text-sm font-medium text-slate-200"
                            >
                                Travellers
                            </label>

                            <input
                                id="travellers"
                                type="number"
                                min={1}
                                max={20}
                                value={travellers}
                                onChange={(event) => {
                                    const nextValue = Number(
                                        event.target.value,
                                    );

                                    if (!Number.isFinite(nextValue)) {
                                        setTravellers(1);
                                        return;
                                    }

                                    setTravellers(
                                        Math.min(
                                            20,
                                            Math.max(1, nextValue),
                                        ),
                                    );
                                }}
                                className="
                                    w-full rounded-xl
                                    border border-white/10 bg-slate-950
                                    px-4 py-3 text-sm text-white
                                    focus:border-cyan-400 focus:outline-none
                                "
                            />
                        </div>

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
                                onChange={(event) => {
                                    setQuestion(event.target.value);
                                }}
                                placeholder="For example: Find me the cheapest flight and hotel options."
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
                            <div
                                role="alert"
                                className="
                                    rounded-xl border border-red-400/20
                                    bg-red-400/10 px-4 py-3
                                    text-sm leading-6 text-red-300
                                "
                            >
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="
                                flex w-full items-center justify-center gap-2
                                rounded-xl bg-cyan-500 px-4 py-3
                                font-semibold text-slate-950
                                transition hover:bg-cyan-400
                                disabled:cursor-not-allowed
                                disabled:opacity-60
                            "
                        >
                            <HiOutlinePaperAirplane className="h-5 w-5" />

                            {isLoading
                                ? "Asking assistant..."
                                : "Ask Travel AI"}
                        </button>
                    </form>
                </section>

                <ChatPanel
                    messages={messages}
                    isLoading={isLoading}
                    onSave={handleSaveResponse}
                    onOpenSaved={handleOpenSavedResponses}
                />
            </div>

            {showSavedResponses && (
                <>
                    <button
                        type="button"
                        aria-label="Close saved responses"
                        onClick={() => {
                            setShowSavedResponses(false);
                        }}
                        className="fixed inset-0 z-40 bg-black/60"
                    />

                    <aside
                        className="
                fixed right-0 top-0 z-50
                h-full w-full max-w-md
                overflow-y-auto
                border-l border-white/10
                bg-slate-950 p-6
                shadow-2xl
            "
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-semibold">
                                    Saved Responses
                                </h2>

                                <p className="mt-1 text-sm text-slate-400">
                                    Responses saved for future reference
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() => {
                                    setShowSavedResponses(false);
                                }}
                                className="
                        rounded-lg px-3 py-2
                        text-slate-400
                        transition
                        hover:bg-white/5
                        hover:text-white
                    "
                            >
                                ✕
                            </button>
                        </div>

                        <div className="mt-6 space-y-4">
                            {savedResponses.length === 0 && (
                                <div
                                    className="
                            rounded-xl
                            border border-white/10
                            p-5 text-center
                            text-sm text-slate-400
                        "
                                >
                                    No saved responses yet.
                                </div>
                            )}

                            {savedResponses.map((savedResponse) => (
                                <SavedResponseCard
                                    key={savedResponse.id}
                                    response={savedResponse}
                                    onDelete={async () => {
                                        try {
                                            await deleteSavedAiResponse(savedResponse.id);

                                            setSavedResponses((currentResponses) =>
                                                currentResponses.filter(
                                                    (response) =>
                                                        response.id !== savedResponse.id,
                                                ),
                                            );
                                        } catch (caughtError) {
                                            console.error(
                                                "Unable to delete saved AI response:",
                                                caughtError,
                                            );

                                            setError(
                                                caughtError instanceof Error
                                                    ? caughtError.message
                                                    : "Unable to delete saved response.",
                                            );
                                        }
                                    }}
                                />
                            ))}
                        </div>
                    </aside>
                </>
            )}
        </main>
    );
}


type FormFieldProps = {
    label: string;
    placeholder: string;
    value: string;
    onChange: (value: string) => void;
    maxLength?: number;
};


function FormField({
    label,
    placeholder,
    value,
    onChange,
    maxLength,
}: FormFieldProps) {
    const inputId = label
        .toLowerCase()
        .replaceAll(" ", "-")
        .replaceAll("/", "-");

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
                maxLength={maxLength}
                onChange={(event) => {
                    onChange(event.target.value);
                }}
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


type DateFieldProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    min?: string;
};


function DateField({
    label,
    value,
    onChange,
    min,
}: DateFieldProps) {
    const inputId = label
        .toLowerCase()
        .replaceAll(" ", "-")
        .replaceAll("/", "-");

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
                type="date"
                value={value}
                min={min}
                onChange={(event) => {
                    onChange(event.target.value);
                }}
                className="
                    w-full rounded-xl
                    border border-white/10 bg-slate-950
                    px-4 py-3 text-sm text-white
                    focus:border-cyan-400 focus:outline-none
                "
            />
        </div>
    );
}


type ChatPanelProps = {
    messages: ChatMessage[];
    isLoading: boolean;
    onSave: (
        message: ChatMessage,
        index: number,
    ) => void;
    onOpenSaved: () => void;
};


function ChatPanel({
    messages,
    isLoading,
    onSave,
    onOpenSaved,
}: ChatPanelProps) {
    return (
        <section className="flex min-h-[650px] flex-col rounded-2xl border border-white/10 bg-slate-900">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-5">
                <div>
                    <h2 className="font-semibold">
                        Conversation
                    </h2>

                    <p className="mt-1 text-sm text-slate-400">
                        Travel-related questions only
                    </p>
                </div>

                <button
                    type="button"
                    onClick={onOpenSaved}
                    className="
            flex items-center gap-2
            rounded-xl border border-white/10
            px-3 py-2 text-sm text-slate-300
            transition hover:border-cyan-400/40
            hover:bg-white/5 hover:text-cyan-300
        "
                >
                    <HiOutlineBookmark className="h-5 w-5" />

                    Saved Responses
                </button>
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
                            Ask about destinations, travel advisories,
                            weather, safety, flights, hotels, activities
                            or itinerary planning.
                        </p>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div
                        key={`${message.role}-${index}`}
                        className={
                            message.role === "user"
                                ? (
                                    "ml-auto max-w-[85%] rounded-2xl "
                                    + "rounded-br-md bg-cyan-500 px-4 "
                                    + "py-3 text-sm text-slate-950"
                                )
                                : (
                                    "mr-auto max-w-[85%] rounded-2xl "
                                    + "rounded-bl-md bg-slate-800 px-4 "
                                    + "py-3 text-sm leading-6 "
                                    + "text-slate-100"
                                )
                        }
                    >
                        {message.role === "assistant" ? (
                            <ReactMarkdown
                                components={{
                                    h1: ({ children }) => (
                                        <h1 className="mb-2 text-lg font-semibold">
                                            {children}
                                        </h1>
                                    ),

                                    h2: ({ children }) => (
                                        <h2 className="mb-2 mt-3 text-base font-semibold">
                                            {children}
                                        </h2>
                                    ),

                                    h3: ({ children }) => (
                                        <h3 className="mb-1.5 mt-3 text-sm font-semibold text-cyan-300">
                                            {children}
                                        </h3>
                                    ),

                                    p: ({ children }) => (
                                        <p className="mb-2 leading-6 last:mb-0">
                                            {children}
                                        </p>
                                    ),

                                    ul: ({ children }) => (
                                        <ul className="mb-2 list-disc space-y-1 pl-5">
                                            {children}
                                        </ul>
                                    ),

                                    ol: ({ children }) => (
                                        <ol className="mb-2 list-decimal space-y-1 pl-5">
                                            {children}
                                        </ol>
                                    ),

                                    li: ({ children }) => (
                                        <li className="leading-6">
                                            {children}
                                        </li>
                                    ),

                                    strong: ({ children }) => (
                                        <strong className="font-semibold text-white">
                                            {children}
                                        </strong>
                                    ),

                                    hr: () => (
                                        <hr className="my-3 border-white/10" />
                                    ),
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        ) : (
                            <p className="whitespace-pre-wrap">
                                {message.content}
                            </p>
                        )}
                        {message.role === "assistant" && (
                            <button
                                type="button"
                                onClick={() => onSave(message, index)}
                                disabled={message.saved}
                                className="
            mt-3 flex items-center gap-1.5
            text-xs font-medium text-slate-400
            transition hover:text-cyan-300
            disabled:text-cyan-400
        "
                            >
                                {message.saved ? (
                                    <HiBookmark className="h-4 w-4" />
                                ) : (
                                    <HiOutlineBookmark className="h-4 w-4" />
                                )}

                                {message.saved
                                    ? "Saved"
                                    : "Save response"}
                            </button>
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

type SavedResponseCardProps = {
    response: SavedAiResponse;
    onDelete: () => void;
};


function SavedResponseCard({
    response,
    onDelete,
}: SavedResponseCardProps) {
    const [expanded, setExpanded] = useState(false);

    return (
        <article
            className="
                rounded-xl
                border border-white/10
                bg-slate-900 p-4
            "
        >
            <h3 className="font-medium text-white">
                {response.title
                    || "Saved travel response"}
            </h3>

            <p className="mt-1 text-xs text-slate-500">
                {new Date(
                    response.saved_at.endsWith("Z")
                        ? response.saved_at
                        : `${response.saved_at}Z`
                ).toLocaleString("en-SG", {
                    timeZone: "Asia/Singapore",
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                })}
            </p>

            {expanded && (
                <div
                    className="
                        mt-4 border-t border-white/10
                        pt-4 text-sm
                        text-slate-300
                    "
                >
                    <ReactMarkdown>
                        {response.ai_response}
                    </ReactMarkdown>
                </div>
            )}

            <div className="mt-4 flex gap-3">
                <button
                    type="button"
                    onClick={() => {
                        setExpanded((current) => !current);
                    }}
                    className="
                        text-xs font-medium
                        text-cyan-400
                        hover:text-cyan-300
                    "
                >
                    {expanded
                        ? "Hide"
                        : "View response"}
                </button>

                <button
                    type="button"
                    onClick={onDelete}
                    className="
                        text-xs font-medium
                        text-red-400
                        hover:text-red-300
                    "
                >
                    Delete
                </button>
            </div>
        </article>
    );
}