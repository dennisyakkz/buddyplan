/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        buddy: {
          teal: "#2C6A6B",
          coral: "#D8745E",
          "teal-dark": "#1F4A4B",
        },
        main: {
          bg: "#F7FAFC",
          card: "#FFFFFF",
          text: "#2D3748",
          muted: "#718096",
          border: "#E2E8F0",
        },
        agenda: {
          rood: { bg: "#FED7D7", text: "#9B2C2C" },
          oranje: { bg: "#FEEBC8", text: "#9C4221" },
          geel: { bg: "#FEFCBF", text: "#744210" },
          groen: { bg: "#C6F6D5", text: "#22543D" },
          blauw: { bg: "#EBF8FF", text: "#2B6CB0" },
          teal: { bg: "#E6FFFA", text: "#234E52" },
          paars: { bg: "#EBF4FF", text: "#4C51BF" },
          bruin: { bg: "#EDF2F7", text: "#4A5568" },
        },
      },
      fontFamily: {
        heading: ['"Plus Jakarta Sans"', "Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
};
