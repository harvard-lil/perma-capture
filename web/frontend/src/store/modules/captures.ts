import Axios from '../../config/axios'
import { TransitionalStates } from '../../constants/captures'
import { snakeToPascal, objectSubset } from '../../lib/helpers'

const URL_ROOT = '/captures/'
const LIMIT = 100

const state = {
  all: [],
  apiContext: {
    count: null,
    next: null,
    previous: null
  }
}

const defaultSort = (prop) => (desc) => (a, b) => {
  // swap the argument order if descending
  if(desc) {
    const originalA = a
    a = b
    b = originalA
  }

  // sort first on the property and second on the id
  return a[prop] < b[prop] ? -1
    : a[prop] > b[prop] ? 1
    : a.id < b.id ? -1
    : a.id > b.id ? 1
    : 0
}

const customSorts = {
  created_at: (desc) => {
    const curriedFn = defaultSort('created_at')(desc)
    return (a, b) =>
      curriedFn({...a, created_at: new Date(a.created_at)}, {...b, created_at: new Date(b.created_at)})
  }
}

const getters = {
  getByProperties: state => (props) =>
    state.all.find(
      obj => Object.keys(props).reduce((t, key) => t && props[key] == obj[key], true)
    ),

  sortedBy: (state) => (prop, desc = true) =>
    state.all.sort((customSorts[prop] || defaultSort(prop))(desc)),

  processing: state => state.all.filter(obj =>
    snakeToPascal(obj.status) in TransitionalStates)
}

const actions = {
  list: ({ commit }, params = {ordering: '-created_at'}) =>
    Axios
      .get(URL_ROOT, {params: params})
      .then(resp => {
        commit('updateApiContext', resp.data)
        commit('replace', resp.data.results);
      }),

  pageForward: ({ commit, state }) =>
    Axios
      .get(state.apiContext.next)
      .then(resp => {
        commit('updateApiContext', resp.data)
        commit('append', resp.data.results)
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
  updateApiContext: (state, apiResponseData) =>
    Object.assign(state.apiContext, objectSubset(Object.keys(state.apiContext), apiResponseData)),

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
