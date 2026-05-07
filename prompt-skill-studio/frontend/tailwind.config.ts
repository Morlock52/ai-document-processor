import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "hsl(228 12% 8%)",
          subtle: "hsl(228 12% 11%)",
          muted: "hsl(228 12% 14%)",
        },
        border: "hsl(228 10% 18%)",
        fg: {
          DEFAULT: "hsl(220 18% 92%)",
          muted: "hsl(220 10% 65%)",
          subtle: "hsl(220 8% 50%)",
        },
        brand: {
          DEFAULT: "hsl(265 90% 67%)",
          fg: "hsl(0 0% 100%)",
        },
        success: "hsl(142 70% 45%)",
        warning: "hsl(38 95% 60%)",
        danger: "hsl(0 80% 60%)",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "Inter", "sans-serif"],
        mono: ["ui-monospace", "JetBrains Mono", "Menlo", "monospace"],
      },
      borderRadius: {
        lg: "0.625rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
