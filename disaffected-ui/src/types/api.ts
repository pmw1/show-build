// API Response Types for Show-Build Application

// Authentication Types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface User {
  username: string
  access_level: 'admin' | 'service' | 'user'
  first_name?: string
  last_name?: string
}

export interface ApiKeyResponse {
  key: string
  client_name: string
  access_level: string
  created_by: string
  created_at: string
}

// Rundown Types
export interface RundownItem {
  type: RundownItemType
  slug: string
  title?: string
  duration?: string
  status?: string
  asset_id?: string
  position?: number
}

export type RundownItemType = 'segment' | 'ad' | 'promo' | 'cta' | 'trans'

export interface RundownResponse {
  episode: string
  items: RundownItem[]
}

// Cue Types
export interface BaseCue {
  slug: string
  duration: string
  timestamp?: string
  assetID?: string
}

export interface VoCue extends BaseCue {
  type: 'VO'
  text: string
  mediaURL?: string
}

export interface NatCue extends BaseCue {
  type: 'NAT'
  description: string
  mediaURL?: string
}

export interface PkgCue extends BaseCue {
  type: 'PKG'
  title: string
  mediaURL?: string
}

export interface GfxCue extends BaseCue {
  type: 'GFX'
  title: string
  description?: string
}

export interface FsqCue extends BaseCue {
  type: 'FSQ'
  text: string
  attribution?: string
}

export interface SotCue extends BaseCue {
  type: 'SOT'
  title: string
  description?: string
  mediaURL?: string
}

// Future cue types
export interface VoxCue extends BaseCue {
  type: 'VOX'
  text: string
  mediaURL?: string
}

export interface MusCue extends BaseCue {
  type: 'MUS'
  title: string
  mediaURL?: string
}

export interface LiveCue extends BaseCue {
  type: 'LIVE'
  title: string
}

export type CueType = VoCue | NatCue | PkgCue | GfxCue | FsqCue | SotCue | VoxCue | MusCue | LiveCue

// Asset Management Types
export interface Asset {
  id: string
  filename: string
  type: string
  path: string
  created_at: string
  size?: number
}

export interface AssetUploadResponse {
  id: string
  filename: string
  path: string
}

// Template Types
export interface Template {
  id: string
  name: string
  type: RundownItemType
  content: string
  created_at: string
  modified_at: string
}

// Episode Types
export interface Episode {
  episode_number: string
  title: string
  airdate?: string
  duration?: string
  status?: string
}

// API Error Response
export interface ApiError {
  detail: string
  status_code: number
}

// Health Check Response
export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  timestamp?: string
}

// Generic API Response Wrapper
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}