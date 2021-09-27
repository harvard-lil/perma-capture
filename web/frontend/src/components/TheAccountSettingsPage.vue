<template>
  <div class="container-full two-col account-page-container">
    <div class="account-info">
      <TheUserForm/>
      <ThePasswordChangeForm/>
    </div>
    <div class="api-info">
      <BaseForm :fields="[{name: 'api-key', label: 'Your API key', value: auth_token.key, readonly: true}]"
                :action="resetToken"
                title="API"
                headingLevel="2"
                submitText="Get a new key"/>
    </div>
  </div>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapState, mapActions} = createNamespacedHelpers('user')

import BaseForm from './BaseForm.vue'
import ThePasswordChangeForm from './ThePasswordChangeForm.vue'
import TheUserForm from './TheUserForm.vue'

export default {
  components: {
    TheUserForm,
    ThePasswordChangeForm,
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
