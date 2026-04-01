/**
 * main.jsx
 * 
 * The entry point for the React application.
 * It renders the root App component, wrapped in providers like LanguageProvider,
 * SOPConfigProvider, and StrictMode for development checks.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import './App.css';
import { LanguageProvider } from './context/LanguageContext';
import { SOPConfigProvider } from './context/SOPConfigContext';

// Create the React root and render the application tree
ReactDOM.createRoot(document.getElementById('root')).render(
  <LanguageProvider>
    <SOPConfigProvider>
      <App />
    </SOPConfigProvider>
  </LanguageProvider>,
);