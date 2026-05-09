import { useMemo } from 'react'
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import type { TradeHistoryItem } from '@/types'

type ChartPoint = {
  date: string
  cumPnl: number
  cumBaseline: number
  winRate: number
}

export function PerformanceChart({ items }: { items: TradeHistoryItem[] }) {
  const data: ChartPoint[] = useMemo(() => {
    const settled = items
      .filter(i => (i.status === 'WIN' || i.status === 'LOSS') && i.actual_pnl != null)
      .sort((a, b) => a.created_at.localeCompare(b.created_at))

    let cumPnl = 0
    let cumBaseline = 0
    let wins = 0
    return settled.map((item, idx) => {
      cumPnl += item.actual_pnl!
      cumBaseline += item.baseline_pnl ?? 0
      if (item.status === 'WIN') wins++
      return {
        date: item.created_at.slice(5, 10),
        cumPnl: Math.round(cumPnl),
        cumBaseline: Math.round(cumBaseline),
        winRate: Math.round((wins / (idx + 1)) * 100),
      }
    })
  }, [items])

  if (data.length === 0) {
    return (
      <p className="text-center text-sm text-gray-400 dark:text-gray-500 py-8">
        決済済みの取引データがありません
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis yAxisId="pnl" tick={{ fontSize: 11 }} unit="円" width={72} />
        <YAxis
          yAxisId="rate"
          orientation="right"
          tick={{ fontSize: 11 }}
          unit="%"
          domain={[0, 100]}
          width={40}
        />
        <Tooltip
          formatter={(value, name) => {
            const v = Number(value)
            if (name === '勝率（右軸）') return [`${v}%`, name]
            return [`${v.toLocaleString()}円`, name]
          }}
        />
        <Legend />
        <Line
          yAxisId="pnl"
          type="monotone"
          dataKey="cumPnl"
          name="累積損益（左軸）"
          stroke="#3b82f6"
          dot={{ r: 3 }}
          strokeWidth={2}
        />
        <Line
          yAxisId="pnl"
          type="monotone"
          dataKey="cumBaseline"
          name="1000通貨基準（左軸）"
          stroke="#9ca3af"
          dot={{ r: 3 }}
          strokeDasharray="4 2"
        />
        <Line
          yAxisId="rate"
          type="monotone"
          dataKey="winRate"
          name="勝率（右軸）"
          stroke="#22c55e"
          dot={{ r: 3 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
