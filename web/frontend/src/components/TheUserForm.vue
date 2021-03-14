<template>
<form @submit.prevent="submit"
      :class="{'was-validated': wasValidated}"
      novalidate>

  <label for="first_name" class="form-label">First name</label>
  <input name="first_name"
         id="first_name"
         v-model="formData.first_name"
         @focus="clearServerError"
         type="text"
         required="required"
         class="form-control"
         :class="{'is-invalid': formServerErrors.first_name}">
  
  <label for="last_name" class="form-label mt-3">Last name</label>
  <input name="last_name"
         id="last_name"
         v-model="formData.last_name"
         @focus="clearServerError"
         type="text"
         required="required"
         class="form-control"
         :class="{'is-invalid': formServerErrors.last_name}">
  
  <label for="email" class="form-label mt-3">Email</label>
  <input name="email"
         id="email"
         v-model="formData.email"
         @focus="clearServerError"
         type="email"
         required="required"
         class="form-control"
         :class="{'is-invalid': formServerErrors.email}">

  <button type="submit" class="btn btn-primary mt-3">Save changes</button>

</form>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

import { assignOverlap } from '../lib/helpers'

export default {
  data: () => ({
    wasValidated: false,
    formData: {
      first_name: null,
      last_name: null,
      email: null
    },
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
    assignOverlap(this.formData, this.$store.state.user)
  }
}
</script>

<style>
</style>
