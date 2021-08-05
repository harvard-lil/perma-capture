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
    displayedCapture: undefined,
    breakpoints: {
      xs: 576-1,
      sm: 768-1,
      md: 992-1,
      lg: 1200-1,
      xl: 1400-1
    },
    windowWidth: 'xl',
  },
  mutations: {
    setDisplayedCapture: (state, capture) => {
      state.displayedCapture = capture;
    },
    setWindowWidth: (state) => {
      if (window.innerWidth <= state.breakpoints.xs) {
        state.windowWidth = 'xs';
      } else if (window.innerWidth <= state.breakpoints.sm) {
        state.windowWidth = 'sm';
      } else if (window.innerWidth <= state.breakpoints.md) {
        state.windowWidth = 'md';
      } else if (window.innerWidth <= state.breakpoints.lg) {
        state.windowWidth = 'lg';
      } else {
        state.windowWidth = 'xl';
      }
    }
  },
  actions: {},
  getters: {
    displayedCapture: (state) => {
      return state.displayedCapture;
    },
    isMobile: (state) => {
      return state.windowWidth === 'md' || state.windowWidth === 'sm' || state.windowWidth === 'xs';
    }
  },
})
