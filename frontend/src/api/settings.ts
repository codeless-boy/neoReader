import api from './index'

export interface SystemSetting {
  key: string
  category: string
  group: string
  label: string
  value: string
  field_type: string
  options?: string // JSON string
  description?: string
  sort_order: number
}

export interface SystemInfo {
  os: string
  platform: string
  cwd: string
  version: string
}

export type SettingsTree = Record<string, Record<string, SystemSetting[]>>

export const getSettings = async (): Promise<SettingsTree> => {
  const response = await api.get<SettingsTree>('/settings/')
  return response.data
}

export const updateSetting = async (key: string, value: string): Promise<SystemSetting> => {
  const response = await api.put<SystemSetting>(`/settings/${key}`, null, {
    params: { value }
  })
  return response.data
}

export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await api.get<SystemInfo>('/settings/system-info')
  return response.data
}
