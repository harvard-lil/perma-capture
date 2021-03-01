import Axios from '../../config/axios'

const URL_ROOT = '/captures/'
const TRANSITIONAL_STATES = ["pending", "in_progress"]

const state = {
  all: []
}

const getters = {
  getByProperties: state => (props) =>
    state.all.find(
      obj => Object.keys(props).reduce((t, key) => t && props[key] == obj[key], true)
    ),

  createdAtDesc: state => state.all.sort((a, b) =>
    new Date(b.created_at) - new Date(a.created_at)),

  processing: state => state.all.filter(obj =>
      TRANSITIONAL_STATES.includes(obj.status))
}

const actions = {
  list: ({ commit }, payload) =>
    Axios
      .get(URL_ROOT)
      .then(resp => {
        commit('replace', resp.data.results);
      }),

  create: ({ commit }, payload) =>
    Axios
      .post(URL_ROOT, payload)
      .then(resp => {
        commit('append', resp.data)
      }),

  read: ({ commit, getters }, payload) =>
    Axios
      .get(`${URL_ROOT}${payload.id}`)
      .then(resp => {
        const existing = getters.getByProperties({id: payload.id})
        existing ?
          commit('update', {obj: existing, vals: resp.data}) :
          commit('append', [resp.data])
      }),

  batchRead: ({ commit, getters }, payload) =>
    Axios
      .get(URL_ROOT, {params: {id__in: payload.map(({ id }) => id)}})
      .then(response => {
        for (const [i, responseCapture] of response.data.results.entries()){
          const existing = getters.getByProperties({id: payload[i].id})
          existing ?
            commit('update', {obj: existing, vals: responseCapture}) :
            commit('append', [responseCapture])
        }
      }),

  eagerCreateAndUpdate: ({ commit, getters }, payload) => {
    commit('append', payload)
    Axios
      .post(URL_ROOT, payload)
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
