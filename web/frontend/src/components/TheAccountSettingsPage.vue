<template>
<TheNavbar/>
<main>
  <div class="row mt-5 gx-5">
    <div class="col">
      <h2>Profile</h2>
      <TheUserForm/>

      <h2>Password</h2>
      <p><router-link :to="{name: 'password_change'}" class="btn btn-primary">Change my password</router-link></p>
    </div>

    <div class="col">
      <h2>API</h2>
      <p>
        <label for="api-key" class="form-label">Your API key</label>
        <input id="api-key" type="text" v-model="auth_token.key" class="form-control mb-3" readonly>
        <button type="button" class="btn btn-primary" @click="resetToken">Get a new key</button>
      </p>
    </div>
  </div>
</main>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState, mapActions } = createNamespacedHelpers('user')

import TheNavbar from './TheNavbar.vue'
import TheUserForm from './TheUserForm.vue'

export default {
  components: {
    TheNavbar,
    TheUserForm
  },
  computed: mapState([
    'auth_token'
  ]),
  methods: {
    ...mapActions(['resetToken'])
  }
}
</script>

<style>
</style>
