<template>
<form @submit.prevent="submit"
      :class="{'was-validated': displayFrontendValidation}"
      novalidate>

  <div v-if="errorCount"
       class="invalid-feedback d-block">
    <p>
      Please correct the following
      <template v-if="errorCount == 1">error</template>
      <strong v-else>{{ errorCount }} errors</strong>:
    </p>

    <ul>
      <li v-for="(errors, fieldName) in serverErrors">
        <template v-if="fieldName != '__all__'">
          <a href="">{{ fieldsWithDefaults.find(field => field.name == fieldName).label }}</a>:
        </template>
        {{ errors.map(({message}) => message).join(', ') }}
      </li>
    </ul>
  </div>

  <template v-for="field in fieldsWithDefaults">
    <label :for="field.name" class="form-label mt-3">{{ field.label }}</label>
    <input :name="field.name"
           :id="field.name"
           v-model="field.value"
           @focus="clearServerError"
           :type="field.type"
           :required="field.required"
           :disabled="field.disabled === true || processing"
           :readonly="field.readonly"
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
  computed: {
    fieldsWithDefaults() {
      return this.fields.map(field => ({
        label: field.name
          .split('_')
          .map((val, i) =>
            !i ? val.charAt(0).toUpperCase() + val.slice(1) : val)
          .join(' '),
        type: 'text',
        readonly: false,
        disabled: false,
        required: true,
        ...field
      }))
    },
    errorCount() {
      return Object.keys(this.serverErrors).length
    }
  },
  methods: {
    ...mapActions(['changePassword']),
    clearServerError(event) {
      delete this.serverErrors[event.target.name]
    },
    submit(event) {
      // if(event.target.checkValidity()){
        this.processing = true
        this.action(new FormData(event.target))
          .catch(error => {
            this.displayFrontendValidation = false
            this.serverErrors = error
          })
          .then(() => this.processing = false)
      // } else {
      //   this.displayFrontendValidation = true
      // }
    }
  }
}
</script>

<style scoped>
</style>
