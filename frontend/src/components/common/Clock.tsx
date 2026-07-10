import { useState, useEffect } from 'react';
import { Clock as ClockIcon } from 'lucide-react';
import { usePreferencesStore, type Region } from '../../store/preferencesStore';

function formatTime(date: Date, region: Region): string {
  try {
    return date.toLocaleTimeString('en-US', {
      timeZone: region,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  }
}

function formatDate(date: Date, region: Region): string {
  try {
    return date.toLocaleDateString('en-US', {
      timeZone: region,
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}

function getRegionLabel(region: Region): string {
  const r = REGIONS.find((r) => r.value === region);
  return r ? `${r.flag} ${r.label}` : region;
}

import { REGIONS } from '../../store/preferencesStore';

export default function Clock() {
  const region = usePreferencesStore((s) => s.region);
  const [now, setNow] = useState(new Date());
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative flex items-center gap-2">
      <div
        className="flex cursor-default items-center gap-2 rounded-lg px-3 py-1.5 text-gray-400 hover:bg-dark-card hover:text-gray-200"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <ClockIcon className="h-4 w-4 shrink-0 text-blue-400" />
        <div className="flex flex-col leading-tight">
          <span className="font-mono text-sm font-medium tabular-nums tracking-wide text-gray-100">
            {formatTime(now, region)}
          </span>
          <span className="text-[10px] text-gray-500">
            {formatDate(now, region)}
          </span>
        </div>
      </div>

      {/* Tooltip showing timezone */}
      {showTooltip && (
        <div className="absolute right-0 top-full mt-2 whitespace-nowrap rounded-lg border border-dark-border bg-dark-card px-3 py-1.5 text-xs text-gray-400 shadow-xl">
          {getRegionLabel(region)}
        </div>
      )}
    </div>
  );
}
