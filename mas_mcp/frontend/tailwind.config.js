/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // MAS-MCP brand colors
        'mas-dark': '#1a1a2e',
        'mas-darker': '#16213e',
        'mas-accent': '#0f3460',
        'mas-highlight': '#e94560',
        'mas-success': '#22c55e',
        'mas-warning': '#f59e0b',
        'mas-error': '#ef4444',
      },
    },
  },
  plugins: [],
};

export default config;
