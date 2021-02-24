<template>
<form ref="form"
      class="capture-form p-3"
      @submit.prevent="submit"
      @keydown.shift.enter.exact.prevent="submit"
      @keydown.meta.enter.exact.prevent="submit">
  <div class="mb-3">
    <label for="requested_urls" class="form-label">URLs</label>
    <textarea v-model="requested_urls" id="requested_urls" class="form-control" rows="3" required="" placeholder="Enter one or more URLs on each line" aria-describedby="urls-errors" aria-invalid="false"></textarea>
  </div>
  
  <div class="mb-3 form-check">
    <input v-model="capture_oembed_view" id="capture_oembed_view" type="checkbox" class="form-check-input">
    <label for="capture_oembed_view" class="form-check-label">Archive Embedded Version (if available)</label>
  </div>
  
  <div class="mb-3">
    <label for="label" class="form-label">Label (Optional)</label>
    <input v-model="label" id="label" type="text" class="form-control">
  </div>
  
  <button type="submit" class="btn btn-primary mb-3">Capture</button>
</form>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('captures')

export default {
  data: () => ({
    requested_urls: '',
    capture_oembed_view: false,
    label: ''
  }),
  computed: {
    formatted_urls() {
      return this.requested_urls.trim().split('\n');
    }
  },
  methods: {
    ...mapActions(['eagerCreateAndUpdate']),
    submit() {
      this.eagerCreateAndUpdate(this.formatted_urls.map(url => ({
        requested_url: url,
        capture_oembed_view: this.capture_oembed_view,
        label: this.label,
        created_at: new Date().toISOString()
      })))
      this.$refs.form.reset()
    }
  }
}
</script>

<style scoped>
.capture-form {
  background: var(--color-background);
  }
</style>
