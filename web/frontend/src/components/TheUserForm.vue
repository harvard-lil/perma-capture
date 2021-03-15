<template>
<Form :fields="fields"
      :action="update"/>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import Form from './Form.vue'

export default {
  components: {
    Form
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

<style scoped>
</style>
