import Axios from '../../config/axios'

interface State {
  all: Array<{}>
}

const state: State = {
  all: []
}

const getters = {
}

const actions = {
  list: ({ commit }, payload) =>
    Axios
      .get('/captures')
      .then(resp => {
        commit('replace', resp.data.results);
      })
}

const mutations = {
  replace: (state: State, payload: Array<{}>) =>
    state.all = payload,

  append: (state: State, payload: Array<{}>) =>
    state.all.push(...payload),

  update: (state: State, payload: {}) =>
    Object.assign(payload.obj, payload.vals),

  destroy: (state: State, payload: {}) =>
    state.all.splice(state.all.indexOf(payload), 1)
};

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
