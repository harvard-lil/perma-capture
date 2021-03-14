<template>
<form @submit.prevent="submit"
      :class="{'was-validated': wasValidated}"
      novalidate>

  <label for="first_name" class="form-label">First name</label>
  <input name="first_name"
         id="first_name"
         v-model="formData.first_name"
         type="text"
         required="required"
         class="form-control">
  
  <label for="last_name" class="form-label mt-3">Last name</label>
  <input name="last_name"
         id="last_name"
         v-model="formData.last_name"
         type="text"
         required="required"
         class="form-control">
  
  <label for="email" class="form-label mt-3">Email</label>
  <input name="email"
         id="email"
         v-model="formData.email"
         type="email"
         required="required"
         class="form-control">

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
    }
  }),
  methods: {
    ...mapActions(['update']),
    submit(event) {
      if(event.target.checkValidity()){
        this.update(new FormData(event.target)).catch(error => {
          this.wasValidated = true
          console.log(error)
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
