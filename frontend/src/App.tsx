import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.tsx";
import ExploreMapPage from "./pages/ExploreMapPage.tsx";
import DestinationDashboardPage from "./pages/DestinationDashboardPage.tsx";
import AboutPage from "./pages/AboutPage.tsx";
import Navbar from "./components/Navbar.tsx";
import TravelPlanningPage from "./pages/TravelPlanningPage";
import SavedTravelPage from "./pages/SavedTravelPage";
import LoginPage from "./pages/LoginPage";
import RegistrationPage from "./pages/RegistrationPage";
import { AuthProvider } from "./context/AuthContext";
import AiAssistantPage from "./pages/AiAssistantPage";
import FloatingAiButton from "./components/FloatingAiButton";


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/map" element={<ExploreMapPage />} />
          <Route path="/planning" element={<TravelPlanningPage />} />
          <Route path="/saved-travel" element={<SavedTravelPage />} />
          <Route path="/about" element={<AboutPage />} />
          {/* Authentication pages */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegistrationPage />} />
          <Route
            path="/destinations/:countryCode"
            element={<DestinationDashboardPage />}
          />
          <Route path="/ai-assistant" element={<AiAssistantPage />} />
        </Routes>

        <FloatingAiButton />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;