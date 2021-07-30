<template>
  <form ref="form"
        class="capture-form"
        @submit.prevent="submit"
        @keydown.shift.enter.exact.prevent="submit"
        @keydown.meta.enter.exact.prevent="submit">
    <div class="form-content">
      <h1>Create a capture for download</h1>
      <h2 class="subtitle">Enter one or more URLs to capture it in a downloadable archive.</h2>
      <div class="mb-3">

        <textarea v-model="requested_urls" id="requested_urls" class="form-control" rows="3" required=""
                  placeholder="Enter one or more URLs on each line" aria-describedby="urls-errors"
                  aria-invalid="false"></textarea>
      </div>

      <!--    <div clas="mb-3 form-check">-->
      <!--      <input v-model="capture_oembed_view" id="capture_oembed_view" type="checkbox" class="form-check-input">-->
      <!--      <label for="capture_oembed_view" class="form-check-label">Archive Embedded Version (if available)</label>-->
      <!--    </div>-->

      <div class="mb-3">
        <!--      <label for="label" class="form-label">Label (Optional)</label>-->
        <input v-model="label" placeholder="Label (Optional)" id="label" type="text" class="form-control">
      </div>
      <div class="form-submit-container">
        <button type="submit" class="btn btn-primary btn-create">Create</button>
        <span class="warning-text">Captures expire <u>four hours</u> after creation.</span>
      </div>
    </div>
  </form>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapActions} = createNamespacedHelpers('captures')


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
  },
}
</script>

<style></style>