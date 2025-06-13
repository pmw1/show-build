// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Vuetify
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export const vuetify = createVuetify({
  components,
  directives,
  theme: {
    themes: {
      light: {
        colors: {
          // Red family
          'red-base': '#F44336',
          'red-accent': '#FF5252',
          'red-dark': '#D32F2F',
          'red-light': '#FFCDD2',

          // Deep Purple family
          'deep-purple-base': '#673AB7',
          'deep-purple-accent': '#7C4DFF',
          'deep-purple-dark': '#512DA8',
          'deep-purple-light': '#D1C4E9',

          // Blue family
          'blue-base': '#2196F3',
          'blue-accent': '#448AFF',
          'blue-dark': '#1976D2',
          'blue-light': '#BBDEFB',

          // Indigo family
          'indigo-base': '#3F51B5',
          'indigo-accent': '#536DFE',
          'indigo-dark': '#303F9F',
          'indigo-light': '#C5CAE9',

          // Teal family
          'teal-base': '#009688',
          'teal-accent': '#64FFDA',
          'teal-dark': '#00796B',
          'teal-light': '#B2DFDB',

          // Green family
          'green-base': '#4CAF50',
          'green-accent': '#69F0AE',
          'green-dark': '#388E3C',
          'green-light': '#C8E6C9',

          // Lime family
          'lime-base': '#CDDC39',
          'lime-accent': '#EEFF41',
          'lime-dark': '#AFB42B',
          'lime-light': '#F0F4C3',

          // Yellow family (add before Grey family)
          'yellow-base': '#FFEB3B',
          'yellow-accent': '#FFD740',
          'yellow-dark': '#FBC02D',
          'yellow-light': '#FFF9C4',

          // Grey family
          'grey-base': '#9E9E9E',
          'grey-accent': '#BDBDBD',
          'grey-dark': '#616161',
          'grey-light': '#F5F5F5',

          // Keep any existing theme colors you need
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00',
        }
      }
    }
  }
})

