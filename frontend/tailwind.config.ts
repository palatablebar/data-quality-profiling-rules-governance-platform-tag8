import type { Config } from 'tailwindcss'

// Only variable references here — every concrete colour lives in
// src/styles/tokens.css as an oklch() token.
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        paper: 'var(--paper)',
        'paper-2': 'var(--paper-2)',
        rule: 'var(--rule-line)',
        ink: 'var(--ink)',
        'ink-soft': 'var(--ink-soft)',
        assay: 'var(--assay)',
        alert: 'var(--alert)',
        'alert-deep': 'var(--alert-deep)',
        low: 'var(--low)',
      },
      fontFamily: {
        display: ['"Libre Caslon Text"', 'Georgia', 'serif'],
        sans: ['"Public Sans"', 'Helvetica', 'sans-serif'],
      },
      letterSpacing: { label: '0.06em' },
    },
  },
  plugins: [],
} satisfies Config
