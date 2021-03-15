<template>
<div class="row mt-5 gx-5">
  <div class="col">
    <h2>Profile</h2>
    <TheUserForm/>
    
    <h2>Password</h2>
    <router-link :to="{name: 'password_change'}" class="btn btn-primary mt-3">
      Change my password
    </router-link>
  </div>
  
  <div class="col">
    <h2>API</h2>
    <BaseForm :fields="[{name: 'api-key', label: 'Your API key', value: auth_token.key, readonly: true}]"
          :action="resetToken"
          submitText="Get a new key"/>
  </div>
</div>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState, mapActions } = createNamespacedHelpers('user')

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

<style scoped>
</style>
