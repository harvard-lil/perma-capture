<template>
<form class="base-form" @submit.prevent="submit" novalidate>
  <div v-if="title"
      role="heading"
      :aria-level="headingLevel"
      :class="['form-heading mb-1', 'h'+headingLevel]">
    {{ title }}
  </div>

  <div v-if="displayValidations && errorCount"
       ref="errorsHeader"
       tabindex="-1"
       class="invalid-field-summary alert alert-danger">

    Please correct the following
    <template v-if="errorCount == 1">error</template>
    <strong v-else>{{ errorCount }} errors</strong>:

    <ul class="invalid-field-list">
      <li v-for="(errorsArray, fieldName) in errors">
        <template v-if="fieldName != '__all__'">
          <a class="alert-link" :href="'#' + getFieldByName(fieldName).id">{{ getFieldByName(fieldName).label }}</a>:
        </template>
        {{ errorsArray.map(({message}) => message).join(', ') }}
      </li>
    </ul>
  </div>

  <template v-for="field in fieldsWithDefaults">
    <div class="form-floating mb-3">
      <input v-model="field.value"
             @blur="checkValidity"
             @invalid="onInvalid"
             :placeholder="field.label"
             :name="field.name"
             :id="field.id"
             :type="field.type"
             :class="['form-control', {'is-invalid': displayValidations && errors[field.name], 'form-control-plaintext': field.readonly}]"
             :required="field.required"
             :disabled="field.disabled === true || processing"
             :readonly="field.readonly"
             :aria-invalid="!!errors[field.name]"
             :aria-describedby="(errors[field.name] || []).map((error, index) => field.id + 'InvalidFeedback' + index)">
      <label :for="field.id" class="form-label">{{ field.label }}</label>
      <div v-for="(error, index) in errors[field.name]"
           :id="field.id + 'InvalidFeedback' + index"
           class="invalid-feedback">
        {{ error.message }}
      </div>
    </div>
  </template>
  
  <button type="submit"
          class="btn btn-primary mt-1"
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
    action: Function,
    title: String,
    headingLevel: {
      type: Number,
      default: 1
    }
  },
  data: () => ({
    processing: false,
    displayValidations: false,
    errors: {}
  }),
  computed: {
    fieldsWithDefaults() {
      return this.fields.map(field => ({
        label: field.name
          .split('_')
          .map((val, i) =>
            !i ? val.charAt(0).toUpperCase() + val.slice(1) : val)
          .join(' '),
        id: field.name + Date.now(),
        type: 'text',
        readonly: false,
        disabled: false,
        required: true,
        ...field
      }))
    },
    errorCount() {
      return Object.keys(this.errors).length
    }
  },
  watch: {
    errorCount(count) {
      if(count && this.displayValidations){
        // use nextTick else the $ref won't be rendered yet
        this.$nextTick(() => this.$refs.errorsHeader.focus())
      }
    }
  },
  methods: {
    ...mapActions(['changePassword']),
    getFieldByName(name) {
      return this.fieldsWithDefaults.find(field => field.name == name)
    },
    checkValidity(e) {
      if(e.target.checkValidity()){
        delete this.errors[e.target.name]
      }
    },
    onInvalid(e) {
      this.errors[e.target.name] = [{message: e.target.validationMessage}]
    },
    collectFrontendErrors() {
      this.errors = {}
      this.$el.querySelectorAll(':invalid').forEach((node) =>
        this.errors[node.name] = [{message: node.validationMessage}])
    },
    submit(event) {
      this.collectFrontendErrors()
      this.displayValidations = true
      if(this.errorCount == 0){
        this.processing = true
        this.action(new FormData(event.target))
          .then(() => this.displayValidations = false)
          .catch(serverErrors => this.errors = serverErrors)
          .then(() => this.processing = false)
      }
    }
  }
}
</script>
