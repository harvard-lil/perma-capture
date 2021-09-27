<template>
<BaseForm :fields="fields"
          :action="update"
          title="Profile"
          headingLevel="2"
          submitText="Update profile"/>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import BaseForm from './BaseForm.vue'

export default {
  components: {
    BaseForm
  },
  data: () => ({
    fields: [
      {name: 'first_name'},
      {name: 'last_name'},
      {name: 'email', type: 'email'}
    ],
  }),
  methods: {
    ...mapActions(['update']),
  },
  created() {
    for(const field of this.fields){
      field.value = this.$store.state.user[field.name]
    }
  }
}
</script>
