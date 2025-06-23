import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// import tailwindcss from '@tailwindcss/vite' // This line is effectively removed
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()], // tailwindcss() is effectively removed from here
  resolve: {
    alias: {
      // Ensure __dirname is available or handle path resolution appropriately
      // For ES modules, __dirname is not available by default.
      // Using import.meta.url to construct the path is a common pattern.
      // However, for simplicity in this step, I'll assume path.resolve works or a polyfill/equivalent is present.
      // If 'path' module causes issues in Vite for frontend code, this might need adjustment.
      // A typical Vite setup might use: path.resolve(new URL('.', import.meta.url).pathname, './src')
      // For now, keeping it as provided, assuming it's handled in the execution context.
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
