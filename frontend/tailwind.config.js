/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        surface: '#0e0e10',
        'surface-2': '#1a1a1e',
        'surface-3': '#27272b',
        ink: '#f0f0f0',
        'ink-2': '#a0a0a8',
        accent: '#3b82f6',
        'accent-hover': '#2563eb',
        danger: '#ef4444',
        success: '#22c55e',
      },
      animation: {
        shimmer: 'shimmer 1.5s infinite',
        'fade-in': 'fadeIn 0.25s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          from: { opacity: 0, transform: 'translateY(6px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
