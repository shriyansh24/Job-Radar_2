interface ScoreRingProps {
  score: number | null
  size?: number
  strokeWidth?: number
}

export default function ScoreRing({ score, size = 40, strokeWidth = 3 }: ScoreRingProps) {
  if (score === null || score === undefined) return null

  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  const getColor = (s: number) => {
    if (s >= 80) return '#10B981'
    if (s >= 60) return '#0070F3'
    if (s >= 40) return '#F5A623'
    return '#E00000'
  }

  const color = getColor(score)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#333333"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <span
        className="absolute font-mono text-text-primary font-semibold"
        style={{ fontSize: size * 0.28 }}
      >
        {Math.round(score)}
      </span>
    </div>
  )
}
