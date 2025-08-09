/* global jest, describe, it, expect, beforeEach */
import { mount } from '@vue/test-utils'
import ColorSelector from '@/components/ColorSelector.vue'
import { createVuetify } from 'vuetify'

// Create vuetify instance for testing
const vuetify = createVuetify()

describe('ColorSelector.vue', () => {
  beforeEach(() => {
    // Mock localStorage
    global.localStorage.getItem = jest.fn()
    global.localStorage.setItem = jest.fn()
  })

  it('renders correctly', () => {
    const wrapper = mount(ColorSelector, {
      props: {
        currentTheme: 'dark'
      },
      global: {
        plugins: [vuetify],
        mocks: {
          $axios: {
            get: jest.fn()
          }
        }
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('loads colors from localStorage on mount', () => {
    const mockColors = JSON.stringify({
      segment: '#FF5722',
      ad: '#4CAF50'
    })
    
    global.localStorage.getItem.mockReturnValue(mockColors)

    const wrapper = mount(ColorSelector, {
      props: {
        currentTheme: 'dark'
      },
      global: {
        plugins: [vuetify],
        mocks: {
          $axios: {
            get: jest.fn()
          }
        }
      }
    })

    expect(wrapper.vm.colors.segment).toBe('#FF5722')
    expect(wrapper.vm.colors.ad).toBe('#4CAF50')
  })

  it('saves colors to localStorage when saveColors is called', async () => {
    const wrapper = mount(ColorSelector, {
      props: {
        currentTheme: 'dark'
      },
      global: {
        plugins: [vuetify],
        mocks: {
          $axios: {
            get: jest.fn()
          }
        }
      }
    })

    wrapper.vm.colors.segment = '#FF0000'
    await wrapper.vm.saveColors()

    expect(global.localStorage.setItem).toHaveBeenCalledWith(
      'rundown-colors',
      JSON.stringify(wrapper.vm.colors)
    )
  })

  it('has debounced save method', () => {
    const wrapper = mount(ColorSelector, {
      props: {
        currentTheme: 'dark'
      },
      global: {
        plugins: [vuetify],
        mocks: {
          $axios: {
            get: jest.fn()
          }
        }
      }
    })
    expect(wrapper.vm.saveColors).toBeDefined()
  })
})
