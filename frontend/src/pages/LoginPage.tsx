import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, LogIn } from "lucide-react";

import { loginUser } from "../services/authApi";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
    // Updates shared auth state after login.
    const { login } = useAuth();

    const navigate = useNavigate();

    // User can type either username or email.
    const [usernameOrEmail, setUsernameOrEmail] = useState("");
    const [password, setPassword] = useState("");

    // Controls whether the password input is hidden or visible.
    const [showPassword, setShowPassword] = useState(false);

    // UI states for loading/error feedback.
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        // Prevents browser page refresh.
        event.preventDefault();

        setError("");
        setIsSubmitting(true);

        try {
            const loginResponse = await loginUser(usernameOrEmail, password);

            // Save token, fetch current user, and update Navbar through AuthContext.
            await login(loginResponse.access_token);

            // Send user back to Travel Planning after login.
            navigate("/planning");
        } catch (error) {
            if (error instanceof Error) {
                setError(error.message);
            } else {
                setError("Failed to log in");
            }
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
        <section className="mx-auto max-w-md rounded-3xl border border-white/10 bg-slate-900/80 p-8 shadow-2xl">
            <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-amber-500 text-slate-950">
                <LogIn size={20} />
            </div>

            <div>
                <h1 className="text-2xl font-bold">Welcome back</h1>
                <p className="text-sm text-slate-400">
                    Log in to save trips, alerts, and travel plans.
                </p>
            </div>
            </div>

            {error && (
            <div className="mb-4 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
                {error}
            </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="mb-2 block text-sm text-slate-300">
                    Username or email
                </label>

                <input
                    type="text"
                    value={usernameOrEmail}
                    onChange={(event) => setUsernameOrEmail(event.target.value)}
                    required
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-amber-500"
                    placeholder="Enter username or email"
                />
            </div>

           <div>
                <label className="mb-2 block text-sm text-slate-300">
                    Password
                </label>

                <div className="relative">
                    <input
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        required
                        className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 pr-12 outline-none focus:border-amber-500"
                        placeholder="Your password"
                    />

                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-white"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                </div>
            </div>

            <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-xl bg-amber-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
                {isSubmitting ? "Logging in..." : "Log in"}
            </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-400">
                New to TravelBuddiez?{" "}
            <Link to="/register" className="font-medium text-amber-400">
                Create account
            </Link>
            </p>
        </section>
        </main>
    );
}

export default LoginPage;