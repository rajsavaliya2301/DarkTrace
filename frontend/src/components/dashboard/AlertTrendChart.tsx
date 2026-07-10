import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import LoadingSpinner from '../common/LoadingSpinner';
import type { AlertTrend } from '../../types';

interface AlertTrendChartProps {
  data: AlertTrend[] | undefined;
  isLoading: boolean;
  isError: boolean;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; stroke: string }>;
  label?: string;
}) => {
  if (active && payload && payload.length && label) {
    return (
      <div className="rounded-lg border border-dark-border bg-dark-card px-3 py-2 shadow-xl">
        <p className="text-xs text-gray-400">{format(parseISO(label), 'MMM dd, yyyy')}</p>
        {payload.map((entry) => (
          <p key={entry.name} className="text-sm font-medium" style={{ color: entry.stroke }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function AlertTrendChart({
  data,
  isLoading,
  isError,
}: AlertTrendChartProps) {
  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center rounded-xl border border-dark-border bg-dark-card">
        <LoadingSpinner />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-[300px] items-center justify-center rounded-xl border border-red-500/20 bg-red-500/5">
        <p className="text-sm text-red-400">Failed to load trend data</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center rounded-xl border border-dark-border bg-dark-card">
        <p className="text-sm text-gray-500">No trend data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-gray-200">
        Alert Trend (7 days)
      </h3>
      <ResponsiveContainer width="100%" height={230}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#374151' }}
            tickFormatter={(val: string) => format(parseISO(val), 'MMM dd')}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="count"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 3, fill: '#3b82f6' }}
            name="Total"
          />
          <Line
            type="monotone"
            dataKey="critical"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ r: 3, fill: '#ef4444' }}
            name="Critical"
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 3, fill: '#f59e0b' }}
            name="High"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
