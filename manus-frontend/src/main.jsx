import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Import Tailwind CSS directives

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <div className="p-4">
      <h1 className="text-xl font-bold text-blue-600">Hello World - Manus Frontend</h1>
      <p>If you see this, Vite, React, and Tailwind CSS are working!</p>
    </div>
  </React.StrictMode>
);
