/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070b14",
          900: "#0c1220",
          800: "#141c2e",
          700: "#1c2740",
        },
        mist: "#c5d0e0",
        accent: {
          DEFAULT: "#7eb8c9",
          muted: "#5a8f9e",
        },
        sage: "#8fbfa8",
      },
      fontFamily: {
        sans: ["Source Sans 3", "system-ui", "sans-serif"],
        display: ["Outfit", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
