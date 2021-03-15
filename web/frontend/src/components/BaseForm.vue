<template>
<form @submit.prevent="submit"
      :class="{'was-validated': displayFrontendValidation}"
      novalidate>

  <div v-for="error in serverErrors.__all__"
       class="invalid-feedback d-block">
    {{ error.message }}
  </div>

  <template v-for="field in fields">
    <label :for="field.name" class="form-label mt-3">{{ field.label || field.name.replace('_', ' ') }}</label>
    <input :name="field.name"
           :id="field.name"
           v-model="field.value"
           @focus="clearServerError"
           :type="field.type || 'text'"
           :required="field.required !== false"
           :disabled="field.disabled === true || processing"
           :readonly="field.readonly === true"
           class="form-control"
           :class="{'is-invalid': serverErrors[field.name]}"
           :aria-describedby="(serverErrors[field.name] || []).map((error, index) => field.name + 'InvalidFeedback' + index)">
    <div v-for="(error, index) in serverErrors[field.name]"
         :id="field.name + 'InvalidFeedback' + index"
         class="invalid-feedback">
      {{ error.message }}
    </div>
  </template>
  
  <button type="submit"
          class="btn btn-primary mt-3"
          :disabled="processing">
    <span v-if="processing" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    {{ submitText }}
  </button>
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
    processing: false,
    displayFrontendValidation: false,
    serverErrors: {}
  }),
  methods: {
    ...mapActions(['changePassword']),
    clearServerError(event) {
      delete this.serverErrors[event.target.name]
    },
    submit(event) {
      if(event.target.checkValidity()){
        this.processing = true
        this.action(new FormData(event.target))
          .catch(error => {
            this.displayFrontendValidation = false
            this.serverErrors = error
          })
          .then(() => this.processing = false)
      } else {
        this.displayFrontendValidation = true
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
