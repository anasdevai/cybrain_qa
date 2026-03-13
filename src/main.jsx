/**
 * main.jsx
 * 
 * The entry point for the React application.
 * It renders the root App component, wrapped in providers like LanguageProvider
 * and StrictMode for development checks.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './App.css'; // Global CSS styles
import { LanguageProvider } from './context/LanguageContext'; // Context provider for localization

// Create the React root and render the application tree
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </React.StrictMode>,
);