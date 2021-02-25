import Axios from '../../config/axios'

const url_root = '/captures/'

const state = {
  all: []
}

const getters = {
  getByProperties: state => (props) =>
    state.all.find(
      obj => Object.keys(props).reduce((t, key) => t && props[key] == obj[key], true)
    )
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

  read: ({ commit, getters }, payload) =>
    Axios
      .get(`${url_root}${payload.id}`)
      .then(resp => {
        const existing = getters.getByProperties({id: payload.id})
        existing ?
          commit('update', {obj: existing, vals: resp.data}) :
          commit('append', resp.data)
      }),

  eagerCreateAndUpdate: ({ commit, getters }, payload) => {
    commit('append', payload)
    Axios
      .post(url_root, payload)
      .then(response => {
        for (const [i, responseCapture] of response.data.entries()){
          commit('update', {obj: getters.getByProperties({created_at: payload[i].created_at}),
                            vals: responseCapture});
        }
      })
  }
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
