/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#091119',
        surface: {
          DEFAULT: '#121D27',
          raised: '#192733',
          hover: '#233442',
        },
        border: '#344754',
        text: {
          primary: '#F2F7FA',
          secondary: '#B9C8D2',
          muted: '#95AAB8',
        },
        accent: {
          DEFAULT: '#5EEAD4',
          dark: '#164F4C',
        },
        inferred: '#F5B95C',
        danger: '#F28B82',
        success: '#7FD6AA',
        focus: '#A8FFF0',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
