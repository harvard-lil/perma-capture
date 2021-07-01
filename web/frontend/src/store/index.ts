import {createStore} from 'vuex'
import globals from './modules/globals'
import user from './modules/user'
import captures from './modules/captures'

export default createStore({
  modules: {
    globals,
    user,
    captures
  },
  state: {
    capture: undefined,
    breakpoints: {
      xs: 576,
      sm: 768,
      md: 992,
      lg: 1200,
      xl: 1400
    },
  },
  mutations: {
    setCapture: (state, capture) => {
      state.capture = capture;
    },
  },
  actions: {},
  getters: {
    capture: (state) => {
      return state.capture;
    },
    screensize: (state) => {
      if (window.innerWidth <= state.breakpoints.xs) {
        return 'xs'
      } else if (window.innerWidth <= state.breakpoints.sm) {
        return 'sm'
      } else if (window.innerWidth <= state.breakpoints.md) {
        return 'md'
      } else if (window.innerWidth <= state.breakpoints.lg) {
        return 'lg'
      } else {
        return 'xl'
      }
    },
    isMobile: (state) => {
      return window.innerWidth < state.breakpoints.sm;
    }
  },
})
