import Axios from '../../config/axios'

const URL_ROOT = '/user/'

const state = {
  ...store_bootstrap.user,
}

const getters = {
}

const actions = {
  resetToken: ({ commit }) =>
    Axios
      .post(`${URL_ROOT}token_reset/`)
      .then(resp => {
        commit('updateToken', resp.data.token)
      }),
}

const mutations = {
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
