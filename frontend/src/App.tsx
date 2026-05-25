// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from './assets/vite.svg'
// import heroImg from './assets/hero.png'
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from './pages/Home.tsx'
import Comingsoon from './pages/Comingsoon.tsx'
import Navbar from "./components/navbar.tsx";

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/map" element={<Comingsoon />} />
        <Route path="/planning" element={<Comingsoon />} />
        <Route path="/about" element={<Comingsoon />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
