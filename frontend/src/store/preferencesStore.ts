import { create } from 'zustand';

export const REGIONS = [
  { value: 'Asia/Kolkata', label: 'India (IST)', flag: '🇮🇳' },
  { value: 'Asia/Karachi', label: 'Pakistan (PKT)', flag: '🇵🇰' },
  { value: 'Asia/Dhaka', label: 'Bangladesh (BST)', flag: '🇧🇩' },
  { value: 'Asia/Kathmandu', label: 'Nepal (NPT)', flag: '🇳🇵' },
  { value: 'Asia/Colombo', label: 'Sri Lanka (SLST)', flag: '🇱🇰' },
  { value: 'Asia/Kabul', label: 'Afghanistan (AFT)', flag: '🇦🇫' },
  { value: 'Asia/Tehran', label: 'Iran (IRST)', flag: '🇮🇷' },
  { value: 'Asia/Riyadh', label: 'Saudi Arabia (AST)', flag: '🇸🇦' },
  { value: 'Asia/Dubai', label: 'UAE (GST)', flag: '🇦🇪' },
  { value: 'Asia/Shanghai', label: 'China (CST)', flag: '🇨🇳' },
  { value: 'Asia/Tokyo', label: 'Japan (JST)', flag: '🇯🇵' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)', flag: '🇸🇬' },
  { value: 'Europe/London', label: 'UK (GMT/BST)', flag: '🇬🇧' },
  { value: 'Europe/Moscow', label: 'Russia (MSK)', flag: '🇷🇺' },
  { value: 'America/New_York', label: 'US East (EST/EDT)', flag: '🇺🇸' },
  { value: 'America/Chicago', label: 'US Central (CST/CDT)', flag: '🇺🇸' },
  { value: 'America/Denver', label: 'US Mountain (MST/MDT)', flag: '🇺🇸' },
  { value: 'America/Los_Angeles', label: 'US West (PST/PDT)', flag: '🇺🇸' },
  { value: 'UTC', label: 'UTC', flag: '🌐' },
] as const;

export type Region = (typeof REGIONS)[number]['value'];

interface PreferencesState {
  region: Region;
  setRegion: (region: Region) => void;
}

const storedRegion = (() => {
  try {
    const saved = localStorage.getItem('darktrace_region');
    if (saved && REGIONS.some((r) => r.value === saved)) return saved as Region;
  } catch {}
  return 'Asia/Kolkata' as Region;
})();

export const usePreferencesStore = create<PreferencesState>((set) => ({
  region: storedRegion,

  setRegion: (region: Region) => {
    localStorage.setItem('darktrace_region', region);
    set({ region });
  },
}));
