<template>
  <div class="container-full two-col login-page-container ">
    <div class="enter-container">
      <BaseForm :title="'Password change'"
                :fields="fields"
                :action="changePassword"/>
    </div>
  </div>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapActions} = createNamespacedHelpers('user')

import BaseForm from './BaseForm.vue'

export default {
  components: {
    BaseForm
  },
  data: () => ({
    fields: [
      {name: 'old_password', type: 'password'},
      {name: 'new_password1', label: 'New password', type: 'password'},
      {name: 'new_password2', label: 'New password confirmation', type: 'password'}
    ]
  }),
  methods: {
    ...mapActions(['changePassword'])
  }
}
</script>

<style lang="scss">
@import "../styles/styles.scss";
@import "../styles/_pages/login-page";
</style>
