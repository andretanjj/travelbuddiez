import { Link } from 'react-router-dom'

function Navbar() {
  const navLink =
    "text-sm font-medium text-white/85 no-underline transition-colors hover:text-blue-600";
  
  return (
    <nav className="flex h-[60px] w-full items-center justify-between bg-black/90 px-[60px]">
      <h1 className="font-['Dancing_Script'] text-xl font-extrabold text-white/85">
        TravelBuddiez
      </h1>

      <div className="flex items-center gap-6">
        <Link className={navLink}to="/">Home</Link>
        <Link className={navLink} to="/map">Travel Map</Link>
        <Link className={navLink} to="/planning">Travel Planning</Link>
        <Link className={navLink} to="/about">About</Link>
      </div>
    </nav>
  );
}

export default Navbar
