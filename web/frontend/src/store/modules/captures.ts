import Axios from '../../config/axios'

const url_root = '/captures/'

const state = {
  all: []
}

const getters = {
}

const actions = {
  list: ({ commit }, payload) =>
    Axios
      .get(url_root)
      .then(resp => {
        commit('replace', resp.data.results);
      }),

  create: ({ commit }, payload) =>
    Axios
      .post(url_root, payload)
      .then(resp => {
        commit('append', resp.data)
      }),
      })
}

const mutations = {
  replace: (state, payload) =>
    state.all = payload,

  append: (state, payload) =>
    state.all.push(...payload),

  update: (state, payload) =>
    Object.assign(payload.obj, payload.vals),

  destroy: (state, payload) =>
    state.all.splice(state.all.indexOf(payload), 1)
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
