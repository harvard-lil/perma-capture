<template>
<form class="capture-form p-3" @submit.prevent="submit">
  <div class="mb-3">
    <label for="urls" class="form-label">URLs</label>
    <textarea v-model="urls" id="urls" class="form-control" rows="3" required="" placeholder="Enter one or more URLs on each line" aria-describedby="urls-errors" aria-invalid="false"></textarea>
  </div>
  
  <div class="mb-3 form-check">
    <input v-model="embed" id="embed" type="checkbox" class="form-check-input">
    <label for="embed" class="form-check-label">Archive Embedded Version (if available)</label>
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
  data() {
    return {
      urls: '',
      embed: false,
      label: ''
    }
  },
  computed: {
    formatted_urls() {
      return this.urls.split('\n');
    }
  },
  methods: {
    ...mapActions(['create']),
    submit() {
      this.create(this.formatted_urls.map(url => ({
        requested_url: url,
        capture_oembed_view: this.embed,
        label: this.label
      })))
    }
  }
}
</script>

<style scoped>
.capture-form {
  background: var(--color-background);
  }
</style>
