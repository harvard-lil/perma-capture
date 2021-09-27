<template>
  <BaseForm title="Change password"
            headingLevel="2"
            :fields="fields"
            :action="changePassword"
            submitText="Change password"/>
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
