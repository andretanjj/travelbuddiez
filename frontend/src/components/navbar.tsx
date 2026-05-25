import { Link } from 'react-router-dom'
import './navbar.css'

// this is the NavBar

function Navbar() {
    return (
        <nav className="navbar">
        <h1 className='logo'>TravelBuddiez</h1>

        <div className='nav-pages'>
          <Link to="/">Home</Link>
          <Link to="/map">Travel Map</Link>
          <Link to="/planning">Travel Planning</Link>
          <Link to="/about">About</Link>
        </div>
      </nav>
    )
}

export default Navbar