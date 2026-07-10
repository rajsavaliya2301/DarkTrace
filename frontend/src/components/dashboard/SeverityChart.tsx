import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { SEVERITY_COLORS, type SeverityLevel } from '../../utils/constants';
import { capitalize } from '../../utils/formatters';
import LoadingSpinner from '../common/LoadingSpinner';

interface SeverityChartProps {
  data: Record<string, number> | undefined;
  isLoading: boolean;
  isError: boolean;
}

const RADIAN = Math.PI / 180;

function renderCustomizedLabel({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
}) {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={11}
      fontWeight={600}
    >
      {(percent * 100).toFixed(0)}%
    </text>
  );
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { color: string } }>;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-dark-border bg-dark-card px-3 py-2 shadow-xl">
        <p className="text-sm font-medium text-gray-200">
          {capitalize(payload[0].name)}
        </p>
        <p className="text-lg font-bold" style={{ color: payload[0].payload.color }}>
          {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

export default function SeverityChart({
  data,
  isLoading,
  isError,
}: SeverityChartProps) {
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
        <p className="text-sm text-red-400">Failed to load chart data</p>
      </div>
    );
  }

  const chartData = Object.entries(data)
    .filter(([key]) => key !== 'total')
    .map(([name, value]) => ({
      name,
      value,
      color: SEVERITY_COLORS[name as SeverityLevel] || '#6b7280',
    }));

  if (chartData.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center rounded-xl border border-dark-border bg-dark-card">
        <p className="text-sm text-gray-500">No severity data available</p>
      </div>
    );
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-5">
      <h3 className="mb-4 text-sm font-semibold text-gray-200">
        Alert Severity Distribution
      </h3>
      <div className="flex items-center justify-center">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={3}
              dataKey="value"
              labelLine={false}
              label={renderCustomizedLabel}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-center text-xs text-gray-500">
        Total: {total.toLocaleString()} alerts
      </p>
    </div>
  );
}
