<template>
<TheMainHeader
  head="Change password"/>
<div class="row justify-content-center">
<Form :fields="fields"
      :action="changePassword"
      class="col-4"/>
</div>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import TheMainHeader from './TheMainHeader.vue'
import Form from './Form.vue'

export default {
  components: {
    TheMainHeader,
    Form
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

<style scoped>
</style>
