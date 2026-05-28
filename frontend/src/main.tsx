import { StrictMode } from 'react' // load React
import { createRoot } from 'react-dom/client' // Load ReactDOM
import './index.css' // load global CSS
import App from './App.tsx' // load App: go to file called App, get its defualt export, and name it App in this file

createRoot(document.getElementById('root')!).render(
  <StrictMode>
      <App />
  </StrictMode>
)
