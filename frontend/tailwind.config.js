/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        // AgentIQ Prime (Light Mode) - default values
        primary: 'var(--color-primary)',
        'on-primary': 'var(--color-on-primary)',
        'primary-container': 'var(--color-primary-container)',
        'on-primary-container': 'var(--color-on-primary-container)',
        'inverse-primary': 'var(--color-inverse-primary)',

        secondary: 'var(--color-secondary)',
        'on-secondary': 'var(--color-on-secondary)',
        'secondary-container': 'var(--color-secondary-container)',
        'on-secondary-container': 'var(--color-on-secondary-container)',
        'secondary-fixed': 'var(--color-secondary-fixed)',

        tertiary: 'var(--color-tertiary)',
        'on-tertiary': 'var(--color-on-tertiary)',
        'tertiary-container': 'var(--color-tertiary-container)',
        'on-tertiary-container': 'var(--color-on-tertiary-container)',

        background: 'var(--color-background)',
        'on-background': 'var(--color-on-background)',

        surface: 'var(--color-surface)',
        'surface-dim': 'var(--color-surface-dim)',
        'surface-bright': 'var(--color-surface-bright)',
        'surface-container-lowest': 'var(--color-surface-container-lowest)',
        'surface-container-low': 'var(--color-surface-container-low)',
        'surface-container': 'var(--color-surface-container)',
        'surface-container-high': 'var(--color-surface-container-high)',
        'surface-container-highest': 'var(--color-surface-container-highest)',
        'surface-variant': 'var(--color-surface-variant)',

        'on-surface': 'var(--color-on-surface)',
        'on-surface-variant': 'var(--color-on-surface-variant)',

        outline: 'var(--color-outline)',
        'outline-variant': 'var(--color-outline-variant)',

        error: 'var(--color-error)',
        'on-error': 'var(--color-on-error)',
        'error-container': 'var(--color-error-container)',
        'on-error-container': 'var(--color-on-error-container)',

        // Tactical accents (dark mode warm tones)
        'tactical-amber': 'var(--color-tactical-amber)',
        'tactical-red': 'var(--color-tactical-red)',

        // Semantic success (bridges both themes)
        success: 'var(--color-success)',
      },

      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },

      fontSize: {
        'display-lg': ['48px', { lineHeight: '56px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-md': ['24px', { lineHeight: '32px', letterSpacing: '-0.005em', fontWeight: '600' }],
        'title-lg': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'title-md': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'body-lg': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label-lg': ['14px', { lineHeight: '20px', fontWeight: '500' }],
        'label-md': ['12px', { lineHeight: '16px', fontWeight: '500' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '700' }],
        'data-mono': ['14px', { lineHeight: '20px', fontWeight: '500', fontFamily: '"JetBrains Mono", monospace' }],
      },

      spacing: {
        'stack-sm': '4px',
        'stack-md': '12px',
        'stack-lg': '24px',
        'gutter': '16px',
        'container-padding': '24px',
      },

      borderRadius: {
        'sm': '4px',
        'DEFAULT': '8px',
        'lg': '16px',
        'full': '9999px',
      },

      boxShadow: {
        'soft': '0px 4px 12px rgba(0, 0, 0, 0.05)',
        'medium': '0px 12px 32px rgba(27, 67, 50, 0.08)',
        'heavy': '0px 16px 48px rgba(0, 0, 0, 0.12)',
        'glow-primary': '0 0 20px var(--glow-primary)',
        'glow-secondary': '0 0 20px var(--glow-secondary)',
        'glow-error': '0 0 20px var(--glow-error)',
      },

      animation: {
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        'spin-slow': 'spin 10s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'orb-breathe': 'orbBreathe 6s ease-in-out infinite',
        'pulse-ring': 'pulseRing 3s cubic-bezier(0.4, 0, 0.2, 1) infinite',
        'scanline': 'scanline 3s linear infinite',
        'waveform': 'waveform 1s ease-in-out infinite',
        'slide-in': 'slideIn 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
        'fade-in': 'fadeIn 0.2s ease',
      },

      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        orbBreathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.6' },
          '50%': { transform: 'scale(1.05)', opacity: '0.8' },
        },
        pulseRing: {
          '0%': { transform: 'scale(0.8)', opacity: '0.8' },
          '100%': { transform: 'scale(2)', opacity: '0' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        waveform: {
          '0%, 100%': { transform: 'scaleY(0.3)' },
          '50%': { transform: 'scaleY(1)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },

      backdropBlur: {
        xs: '2px',
      },

      transitionDuration: {
        '250': '250ms',
      },
    },
  },
  plugins: [],
}
