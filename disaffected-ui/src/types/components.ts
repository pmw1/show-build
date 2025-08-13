// Component-specific Types for Vue Components

import type { RouteLocationNormalized } from 'vue-router'

// Modal Props
export interface BaseModalProps {
  show: boolean
  episode?: string
  duplicateSlugs?: string[]
}

export interface CueModalEmits {
  (event: 'submit', data: any): void
  (event: 'update:show', value: boolean): void
}

// ColorSelector Types
export interface ColorOption {
  name: string
  value: string
  class: string
}

export interface ThemeColorMap {
  [key: string]: {
    primary: string
    secondary?: string
    accent?: string
    background?: string
    text?: string
  }
}

// StackOrganizer Types  
export interface StackOrganizerProps {
  episode: string
  showRundownPanel?: boolean
  rundownPanelWidth?: 'narrow' | 'wide'
}

export interface StackOrganizerEmits {
  (event: 'select-item', index: number): void
  (event: 'edit-item', index: number): void
  (event: 'drag-start', index: number): void
  (event: 'drag-over', index: number): void
  (event: 'drag-drop', index: number): void
  (event: 'save-rundown'): void
}

// ContentEditor Types
export interface ContentEditorProps {
  episode: string
  selectedItemIndex?: number
  editingItemIndex?: number
}

export interface ContentEditorEmits {
  (event: 'content-change', content: string): void
  (event: 'save-content'): void
}

// Authentication Store Types
export interface AuthState {
  isAuthenticated: boolean
  currentUser: any
  token: string | null
  tokenExpiry: number | null
}

export interface AuthActions {
  login(credentials: { username: string; password: string }): Promise<boolean>
  logout(): void
  checkAuthStatus(): boolean
  refreshToken?(): Promise<boolean>
}

// Router Types
export interface RouteParams {
  episode?: string
  [key: string]: string | undefined
}

export interface NavigationGuardNext {
  (to?: RouteLocationNormalized | boolean | Error): void
}

// Form Validation Types
export type ValidationRule = (value: any) => boolean | string

export interface FormValidation {
  [fieldName: string]: ValidationRule[]
}

// Toast Notification Types
export interface ToastOptions {
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

// Vuetify Theme Types (extending)
declare module 'vuetify' {
  interface ThemeOptions {
    rundownColors?: ThemeColorMap
  }
}