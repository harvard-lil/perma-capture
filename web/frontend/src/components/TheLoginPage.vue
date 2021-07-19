<template>
  <div class="container-full login-page-container">
    <WelcomeMessage/>
    <div class="enter-container">
      <BaseForm :title="'Log in'"
                :fields="fields"
                submitText="Log in"
                :action="doLogin"/>

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
import {createNamespacedHelpers} from 'vuex'

const {mapActions} = createNamespacedHelpers('user')
import WelcomeMessage from './WelcomeMessage.vue'

import BaseForm from './BaseForm.vue'

export default {
  components: {
    BaseForm,
    WelcomeMessage,
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
