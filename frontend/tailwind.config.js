/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontSize: {
        'elderly-base': '1.125rem', // 18px standard base font size for elderly legibility
        'elderly-lg': '1.25rem',   // 20px
        'elderly-xl': '1.5rem',    // 24px
      }
    },
  },
  plugins: [],
}
