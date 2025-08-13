/* global jest, describe, it, expect */
import { mount } from '@vue/test-utils'
import StackOrganizer from '@/components/StackOrganizer.vue'
import { createVuetify } from 'vuetify'

const vuetify = createVuetify()

describe('StackOrganizer.vue', () => {
  it('renders correctly', () => {
    const wrapper = mount(StackOrganizer, {
      props: { episode: '0228' },
      global: { 
        plugins: [vuetify],
        mocks: { $axios: { get: jest.fn() } } 
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('displays segments correctly', async () => {
    const wrapper = mount(StackOrganizer, {
      props: { episode: '0228' },
      global: { 
        plugins: [vuetify],
        mocks: { $axios: { get: jest.fn() } } 
      },
      data: () => ({
        segments: [
          { filename: 'test-segment', type: 'segment', duration: '00:02:30', slug: 'test-segment' }
        ]
      })
    })
    expect(wrapper.vm.segments).toHaveLength(1)
    expect(wrapper.vm.segments[0].type).toBe('segment')
  })

  it('uses standard rundown item types', () => {
    const wrapper = mount(StackOrganizer, {
      props: { episode: '0228' },
      global: { 
        plugins: [vuetify],
        mocks: { $axios: { get: jest.fn() } } 
      }
    })
    
    const expectedTypes = ['segment', 'ad', 'promo', 'cta', 'trans', 'unknown']
    const actualTypes = wrapper.vm.itemTypes.map(type => type.value)
    expect(actualTypes).toEqual(expectedTypes)
  })

  it('calculates segment counts correctly', async () => {
    const wrapper = mount(StackOrganizer, {
      props: { episode: '0228' },
      global: { 
        plugins: [vuetify],
        mocks: { $axios: { get: jest.fn() } } 
      },
      data: () => ({
        segments: [
          { filename: 'segment1', type: 'segment', duration: '00:02:30' },
          { filename: 'ad1', type: 'ad', duration: '00:01:00' },
          { filename: 'segment2', type: 'segment', duration: '00:03:00' }
        ]
      })
    })
    
    expect(wrapper.vm.segmentCount).toBe(2)
    expect(wrapper.vm.advertCount).toBe(1)
  })
})
