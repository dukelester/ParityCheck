interface LogoProps {
  /** Size in pixels. Default 36 for header, 28 for footer. */
  size?: number
  /** Optional className for the wrapper */
  className?: string
}

export function Logo({ size = 36, className = '' }: LogoProps) {
  const uid = `logo-${size}`
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <defs>
        <linearGradient id={`${uid}-bg`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--color-accent)" />
          <stop offset="100%" stopColor="var(--color-accent-muted)" />
        </linearGradient>
        <linearGradient id={`${uid}-shine`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.25)" />
          <stop offset="60%" stopColor="rgba(255,255,255,0.05)" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      {/* Shield - badge-style, distinctive shape */}
      <path
        d="M20 3.5L7 8.5v10c0 8 6 14.5 13 16 7-1.5 13-8 13-16v-10L20 3.5z"
        fill={`url(#${uid}-bg)`}
        stroke="rgba(0,212,170,0.5)"
        strokeWidth="0.6"
        strokeLinejoin="round"
      />
      {/* Inner shine for depth */}
      <path
        d="M20 6L9 10.5v7.5c0 6 4.5 11 11 12.5V6z"
        fill={`url(#${uid}-shine)`}
      />
      {/* Parity symbol ≡ - bold, centered */}
      <path
        d="M12 13.5h16v1.5H12v-1.5zm0 4.25h16v1.5H12v-1.5zm0 4.25h16v1.5H12v-1.5z"
        fill="var(--color-bg)"
      />
    </svg>
  )
}
