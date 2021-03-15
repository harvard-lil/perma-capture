<template>
<form @submit.prevent="submit"
      :class="{'was-validated': wasValidated}"
      novalidate>
  
  <template v-for="field in fields">
    <label :for="field.name" class="form-label mt-3">{{ field.label || field.name.replace('_', ' ') }}</label>
    <input :name="field.name"
           :id="field.name"
           v-model="field.value"
           @focus="clearServerError"
           :type="field.type || 'text'"
           required
           class="form-control"
           :class="{'is-invalid': formServerErrors[field.name]}">
  </template>

  <button type="submit" class="btn btn-primary mt-3">Save changes</button>

</form>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import { assignOverlap } from '../lib/helpers'

export default {
  data: () => ({
    fields: [
      {name: 'first_name'},
      {name: 'last_name'},
      {name: 'email', type: 'email'}
    ],
    wasValidated: false,
    formServerErrors: {}
  }),
  methods: {
    ...mapActions(['update']),
    clearServerError(event) {
      delete this.formServerErrors[event.target.name]
    },
    submit(event) {
      if(event.target.checkValidity()){
        this.update(new FormData(event.target)).catch(error => {
          this.wasValidated = true
          this.formServerErrors = error
        })
      } else {
        this.wasValidated = true
      }
    }
  },
  created() {
    for(const field of this.fields){
      field.value = this.$store.state.user[field.name]
    }
  }
}
</script>

<style scoped>
.form-label {
  text-transform: capitalize;
}
</style>
