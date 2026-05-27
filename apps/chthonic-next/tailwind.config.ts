// @SID: SCRIPT_TAILWIND_CONFIG_V1
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Decorator Theme (Gold/Alchemy)
        obsidian: '#060606',
        ember: '#d07b38',
        brass: '#b19f52',
        chalk: '#f3efe7',
        
        // Orackla Theme (Nigredo/Viscera)
        'orackla-void': '#050505',
        'orackla-crimson': '#8B0000',
        'orackla-oil': '#0A0A0A',
        'orackla-pulse': '#FF4500',

        // Umeko Theme (Albedo/Respiratory)
        'umeko-ivory': '#F3F7FA',
        'umeko-silver': '#D6E0EA',
        'umeko-mist': '#B8C8D8',
        'umeko-breath': '#7DD3FC',
      },
      backgroundImage: {
        sediment:
          'radial-gradient(circle at 20% 20%, rgba(208,123,56,0.20), transparent 45%), radial-gradient(circle at 80% 0%, rgba(177,159,82,0.18), transparent 38%), radial-gradient(circle at 50% 100%, rgba(106,74,45,0.32), transparent 55%)',
        viscera:
          'radial-gradient(circle at 50% 50%, rgba(139,0,0,0.15), transparent 60%), linear-gradient(to bottom, #050505, #0A0A0A)',
        alveolar:
          'radial-gradient(circle at 20% 20%, rgba(255,255,255,0.85), transparent 40%), radial-gradient(circle at 80% 35%, rgba(125,211,252,0.28), transparent 48%), linear-gradient(145deg, #F3F7FA, #D6E0EA)',
      },
      boxShadow: {
        reactor: '0 0 0 1px rgba(177,159,82,0.35), 0 24px 48px rgba(0,0,0,0.55)',
        pulse: '0 0 15px 2px rgba(255, 69, 0, 0.4)',
        breath: '0 0 0 1px rgba(184,200,216,0.8), 0 18px 40px rgba(107,114,128,0.26), inset 0 0 24px rgba(255,255,255,0.55)',
      },
      fontFamily: {
        display: ['"IBM Plex Sans"', '"Segoe UI"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Cascadia Code"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow-viscous': 'flow 10s linear infinite',
        'breath-cycle': 'breath 6s ease-in-out infinite',
        'mist-drift': 'mist 12s linear infinite',
      },
      keyframes: {
        flow: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        breath: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.88' },
          '50%': { transform: 'scale(1.08)', opacity: '1' },
        },
        mist: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '100% 50%' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
