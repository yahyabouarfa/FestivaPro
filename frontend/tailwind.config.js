/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        night: "rgb(var(--color-night) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        secondary: "rgb(var(--color-secondary) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)"
      },
      boxShadow: {
        glow: "var(--shadow-glow)",
        glass: "0 18px 60px rgb(0 0 0 / 0.35)"
      }
    }
  },
  plugins: []
};
