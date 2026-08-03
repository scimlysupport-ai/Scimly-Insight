/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Scimly brand palette — used consistently across the app
        scimly: {
          bg: "#0B1120",
          surface: "#121A2B",
          border: "#1F2A40",
          primary: "#5B8DEF",
          accent: "#22D3AA",
          text: "#E5E9F0",
          muted: "#8B96A8",
        },
      },
      fontFamily: {
        display: ["'Sora'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
