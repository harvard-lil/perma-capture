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
           :class="{'is-invalid': serverErrors[field.name]}">
    <div v-for="error in serverErrors[field.name]" class="invalid-feedback">{{ error.message }}</div>
  </template>
  
  <button type="submit" class="btn btn-primary mt-3">{{ submitText }}</button>
</form>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('user')

export default {
  props: {
    fields: Array,
    submitText: {
      type: String,
      default: 'Submit'
    },
    action: Function
  },
  data: () => ({
    wasValidated: false,
    serverErrors: {}
  }),
  methods: {
    ...mapActions(['changePassword']),
    clearServerError(event) {
      delete this.serverErrors[event.target.name]
    },
    submit(event) {
      if(event.target.checkValidity()){
        this.action(new FormData(event.target)).catch(error => {
          this.wasValidated = false
          this.serverErrors = error
        })
      } else {
        this.wasValidated = true
      }
    }
  }
}
</script>

<style scoped>
  .form-label {
    text-transform: capitalize;
  }
</style>
