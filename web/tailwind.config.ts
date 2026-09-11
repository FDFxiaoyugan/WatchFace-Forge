import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forge: {
          bg: "#101318",
          card: "#1b1f24",
          border: "#44474e",
          accent: "#a8c7fa",
          text: "#e3e2e6",
          muted: "#c4c6d0",
        },
      },
    },
  },
  plugins: [],
};

export default config;
