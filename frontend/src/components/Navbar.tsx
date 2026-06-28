import { Link, NavLink, useNavigate } from "react-router-dom";
import { FiGlobe } from "react-icons/fi";
import { useAuth } from "../context/AuthContext";

function Navbar() {
    const navigate = useNavigate();

    // Reads shared auth state from AuthContext.
    const { user, isLoading, logout } = useAuth();

    const navLink = ({ isActive }: { isActive: boolean }) =>
        `
        rounded-full px-4 py-2 text-sm font-medium no-underline transition-all
        ${
            isActive
                ? "bg-white/10 text-white"
                : "text-blue-100/75 hover:bg-white/5 hover:text-white"
        }
        `;

    function handleLogout() {
        // Clears token and current user from AuthContext.
        logout();

        // Sends user back to home page.
        navigate("/");
    }

    return (
        <nav
            className="
                sticky top-0 z-40 flex h-[68px] w-full items-center justify-between
                border-b border-white/10 bg-[#070b16]/90 px-6 backdrop-blur-md
                md:px-[60px]
            "
        >
            <Link to="/" className="flex items-center gap-3 no-underline">
                <div
                    className="
                        flex h-9 w-9 items-center justify-center rounded-full
                        bg-[#d9964a] text-black shadow-[0_0_24px_rgba(217,150,74,0.25)]
                    "
                >
                    <FiGlobe className="h-5 w-5" />
                </div>

                <h1 className="font-['Playfair_Display'] text-xl font-bold text-white">
                    Travel<span className="text-[#d9964a]">Buddiez</span>
                </h1>
            </Link>

            <div className="hidden items-center gap-2 md:flex">
                <NavLink className={navLink} to="/">
                    Home
                </NavLink>

                <NavLink className={navLink} to="/map">
                    Travel Map
                </NavLink>

                <NavLink className={navLink} to="/planning">
                    Travel Planning
                </NavLink>

                <NavLink className={navLink} to="/about">
                    About
                </NavLink>

                {/* While checking saved token, avoid showing wrong login/logout buttons. */}
                {isLoading ? null : user === null ? (
                    <>
                        <NavLink className={navLink} to="/login">
                            Login
                        </NavLink>

                        <NavLink className={navLink} to="/register">
                            Register
                        </NavLink>
                    </>
                ) : (
                    <div className="ml-3 flex items-center gap-3">
                        <span className="text-sm text-blue-100/75">
                            Welcome, {user.username}
                        </span>

                        <button
                            type="button"
                            onClick={handleLogout}
                            className="rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-blue-100/75 transition hover:bg-white/5 hover:text-white"
                        >
                            Logout
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
}

export default Navbar;