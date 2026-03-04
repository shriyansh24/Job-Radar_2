import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface SourceBreakdownChartProps {
  data: { source: string; count: number }[]
}

export default function SourceBreakdownChart({ data }: SourceBreakdownChartProps) {
  if (data.length === 0) {
    return <div className="text-center text-text-secondary py-8 text-sm">No data yet</div>
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <XAxis dataKey="source" tick={{ fontSize: 11, fill: '#888' }} />
        <YAxis tick={{ fontSize: 11, fill: '#888' }} />
        <Tooltip
          contentStyle={{
            background: '#111',
            border: '1px solid #333',
            borderRadius: 8,
            fontSize: 12,
            color: '#EDEDED',
          }}
        />
        <Bar dataKey="count" fill="#0070F3" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
