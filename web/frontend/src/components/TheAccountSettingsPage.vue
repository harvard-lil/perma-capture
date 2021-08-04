<template>
  <div class="container-full two-col account-page-container">
    <div class="account-info">
      <h1>Profile</h1>
      <TheUserForm/>

      <router-link :to="{name: 'password_change'}" class="btn btn-primary mt-3">
        Change my password
      </router-link>

    </div>
    <div class="api-info">
      <h1>API</h1>
      <BaseForm :fields="[{name: 'api-key', label: 'Your API key', value: auth_token.key, readonly: true}]"
                :action="resetToken"
                submitText="Get a new key"/>
    </div>
  </div>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapState, mapActions} = createNamespacedHelpers('user')

import BaseForm from './BaseForm.vue'
import TheUserForm from './TheUserForm.vue'

export default {
  components: {
    TheUserForm,
    BaseForm
  },
  computed: mapState([
    'auth_token'
  ]),
  methods: {
    ...mapActions(['resetToken'])
  }
}
</script>


<style lang="scss">
@import "../styles/styles.scss";
@import "../styles/_pages/account-page";
</style>
