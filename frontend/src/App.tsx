import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.tsx";
import ExploreMapPage from "./pages/ExploreMapPage.tsx";
import DestinationDashboardPage from "./pages/DestinationDashboardPage.tsx";
import ComingSoon from "./pages/ComingSoon.tsx";
import Navbar from "./components/Navbar.tsx";


function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/map" element={<ExploreMapPage />} />
        <Route path="/planning" element={<ComingSoon />} />
        <Route path="/about" element={<ComingSoon />} />
        <Route
          path="/destinations/:countryCode"
          element={<DestinationDashboardPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;