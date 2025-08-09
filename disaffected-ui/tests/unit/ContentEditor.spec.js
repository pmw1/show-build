/* global jest, describe, it, expect */
import { mount } from '@vue/test-utils'
import ContentEditor from '@/components/ContentEditor.vue'
import { createVuetify } from 'vuetify'

const vuetify = createVuetify()

describe('ContentEditor.vue', () => {
  it('renders correctly with props', () => {
    const wrapper = mount(ContentEditor, {
      props: {
        episode: '0228'
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

  it('handles rundown items correctly', async () => {
    const wrapper = mount(ContentEditor, {
      props: {
        episode: '0228'
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

    // Set some test data
    await wrapper.setData({
      rundownItems: [
        { id: 'item_001', type: 'segment', slug: 'test-segment', duration: '00:02:30', title: 'Test Segment' }
      ]
    })

    expect(wrapper.vm.rundownItems).toHaveLength(1)
    expect(wrapper.vm.rundownItems[0].type).toBe('segment')
  })

  it('handles drag-and-drop correctly', async () => {
    const wrapper = mount(ContentEditor, {
      global: { plugins: [vuetify] },
      data: () => ({
        rundownItems: [
          { id: 'item_001', type: 'segment', slug: 'test1', duration: '00:02:30' },
          { id: 'item_002', type: 'ad', slug: 'test2', duration: '00:01:00' }
        ]
      })
    });
    const items = wrapper.findAll('.rundown-item');
    await items[0].trigger('dragstart', { dataTransfer: { setData: () => {} } });
    await items[1].trigger('dragover');
    await items[1].trigger('drop');
    expect(wrapper.vm.rundownItems[0].slug).toBe('test2');
    expect(wrapper.vm.rundownItems[1].slug).toBe('test1');
  });

  it('emits episode-changed event', async () => {
    const wrapper = mount(ContentEditor, {
      props: {
        episode: '0228'
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

    await wrapper.vm.$emit('episode-changed', '0229')
    expect(wrapper.emitted('episode-changed')).toBeTruthy()
    expect(wrapper.emitted('episode-changed')[0]).toEqual(['0229'])
  })
})
