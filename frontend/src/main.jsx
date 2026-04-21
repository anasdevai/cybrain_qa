/**
 * main.jsx
 * 
 * The entry point for the React application.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './assets/styles/index.css';
import './assets/styles/global.css';
import { LanguageProvider } from './context/LanguageContext';
import { SOPConfigProvider } from './context/SOPConfigContext';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LanguageProvider>
      <SOPConfigProvider>
        <App />
      </SOPConfigProvider>
    </LanguageProvider>
  </React.StrictMode>,
);