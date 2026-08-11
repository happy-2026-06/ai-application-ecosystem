/**
 * Design tokens for 视界短视频工坊 — Cinematic Gold Theme.
 * Import from this file when components need programmatic access to colors.
 */

export const COLORS = {
  primary: '#C8A951',
  primaryHover: '#B8953A',
  primaryLight: '#F5E6C8',

  bgLight: '#FAF9F4',
  bgCardLight: '#FFFDF8',
  bgSurfaceLight: '#F0EEE6',

  bgDark: '#0D0D14',
  bgCardDark: '#1A1A25',
  bgSurfaceDark: '#22222E',

  textLight: '#2C2C3A',
  textSecondaryLight: '#6E6E78',
  textMutedLight: '#A0A0A8',

  textDark: '#E8E8F0',
  textSecondaryDark: '#9999A8',
  textMutedDark: '#6A6A78',

  borderLight: '#E8E4D8',
  borderDark: '#2A2A35',
} as const

/** Platform brand colors */
export const PLATFORM_COLORS: Record<string, string> = {
  '抖音': '#FF0050',
  '小红书': '#FF2442',
  'B站': '#FB7299',
  '视频号': '#07C160',
  '快手': '#FF4906',
}

export const PLATFORM_MAP = [
  { key: 'douyin', label: '抖音', color: '#FF0050' },
  { key: 'xiaohongshu', label: '小红书', color: '#FF2442' },
  { key: 'bilibili', label: 'B站', color: '#FB7299' },
  { key: 'shipinhao', label: '视频号', color: '#07C160' },
  { key: 'kuaishou', label: '快手', color: '#FF4906' },
] as const
