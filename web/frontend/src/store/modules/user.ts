import Axios from '../../config/axios'

const URL_ROOT = '/user/'

const state = {
  ...store_bootstrap.user,
}

const getters = {}

const actions = {
  signup: (_context, payload) =>
      Axios
          .post(`/sign-up/`, payload, {headers: {"Content-Type": "multipart/form-data"}}),

  update: ({commit}, payload) =>
      Axios
          .post(`${URL_ROOT}account/`, payload, {headers: {"Content-Type": "multipart/form-data"}})
          .then(resp => {
            commit('update', resp.data.form.data)
          }),

  login: (_context, payload) =>
      Axios
          .post(`${URL_ROOT}login/`, payload, {headers: {"Content-Type": "multipart/form-data"}}),

  resetPassword: (_context, payload) =>
      Axios
          .post(`${URL_ROOT}password_reset/`, payload, {headers: {"Content-Type": "multipart/form-data"}}),

  changePassword: (_context, payload) =>
      Axios
          .post(`${URL_ROOT}password_change/`, payload, {headers: {"Content-Type": "multipart/form-data"}}),

  resetToken: ({commit}) =>
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
