<template>
<TheMainHeader
  head="Log in"/>
<div class="row justify-content-center">
  <div class="col-4">
    <BaseForm :fields="fields"
              submitText="Log in"
              :action="doLogin"/>
    
    <hr>
    
    <p class="small">
      Don't have an account?
      <router-link :to="{name: 'sign_up'}">Sign up</router-link>
    </p>
    <p class="small">
      Forgot your password?
      <router-link :to="{name: 'password_reset'}">Reset password</router-link>
    </p>
  </div>
</div>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import TheMainHeader from './TheMainHeader.vue'
import BaseForm from './BaseForm.vue'

export default {
  components: {
    TheMainHeader,
    BaseForm
  },
  data: () => ({
    fields: [
      {name: 'username', label: 'Email'},
      {name: 'password', type: 'password'}
    ]
  }),
  methods: {
    ...mapActions(['login']),
    doLogin(params) {
      return this.login(params).then(() => window.location = '/')
    }
  }
}
</script>

<style scoped>
</style>
