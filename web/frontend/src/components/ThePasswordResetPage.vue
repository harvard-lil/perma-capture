<template>
<div class="container">
  <TheMainHeader
    head="Forgot your password?"
    subhead="We'll email you instructions for setting a new one."/>
  <div class="row justify-content-center">
    <BaseForm :fields="fields"
              :action="resetPassword"
              submitText="Reset my password"
              class="col-lg-4 col-md-7 col-9"/>
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
      {name: 'email', type: 'email'}
    ]
  }),
  methods: {
    ...mapActions(['resetPassword'])
  }
}
</script>

<style>
</style>
