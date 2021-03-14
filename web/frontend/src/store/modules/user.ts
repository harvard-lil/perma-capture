import Axios from '../../config/axios'

const URL_ROOT = '/user/'

const state = {
  ...store_bootstrap.user,
}

const getters = {
}

const actions = {
  update: ({ commit }, payload) =>
    Axios
      .post(`${URL_ROOT}account/`, payload, {headers: {"Content-Type": "multipart/form-data"}})
      .then(resp => {
        commit('update', resp.data.form.form.data)
      }),

  resetToken: ({ commit }) =>
    Axios
      .post(`${URL_ROOT}token_reset/`)
      .then(resp => {
        commit('updateToken', resp.data.token)
      }),
}

const mutations = {
  update: (state, payload) =>
    Object.assign(state, payload),

  updateToken: (state, payload) =>
    state.auth_token.key = payload
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
