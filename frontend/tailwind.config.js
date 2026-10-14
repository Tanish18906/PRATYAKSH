/** @type {import('tailwindcss').Config} */
// Colours map to the CSS variables in src/index.css (docs/ui-REDESIGN/DESIGN_SYSTEM.md)
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        'surface-2': 'var(--surface-2)',
        line: 'var(--line)',
        'line-strong': 'var(--line-strong)',
        ink: 'var(--ink)',
        'ink-2': 'var(--ink-2)',
        'ink-3': 'var(--ink-3)',
        accent: 'var(--accent)',
        'accent-hover': 'var(--accent-hover)',
        'accent-tint': 'var(--accent-tint)',
        observed: 'var(--observed)',
        inferred: 'var(--inferred)',
        'inferred-text': 'var(--inferred-text)',
        'inferred-tint': 'var(--inferred-tint)',
        leak: 'var(--leak)',
        'leak-tint': 'var(--leak-tint)',
        ok: 'var(--ok)',
        'ok-tint': 'var(--ok-tint)',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        card: 'var(--radius)',
        ctl: 'var(--radius-sm)',
      },
      boxShadow: {
        pop: 'var(--shadow-pop)',
      },
      screens: {
        wide: '1600px',
      },
    },
  },
  plugins: [],
};
