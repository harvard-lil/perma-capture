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
                  placeholder="Enter one or more URLs on each line"
                  aria-label="Enter one or more URLs on each line"></textarea>
      </div>

      <div class="mb-3">
        <input v-model="label" aria-label="Label (Optional)" placeholder="Label (Optional)" id="label" type="text" class="form-control">
      </div>

      <div class="mb-3 accordion" id="advanced-options-wrapper">
        <div class="accordion-item">
          <div class="accordion-header" id="toggle-advanced-options">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#advanced-options" aria-expanded="true" aria-controls="advanced-options">
              Advanced Options
            </button>
          </div>
          <div id="advanced-options" class="accordion-collapse collapse" aria-labelledby="toggle-advanced-options" data-bs-parent="#advanced-options-wrapper">
            <div class="accordion-body">
              <div clas="form-check">
                <input name="include_raw_exchanges" type="hidden" value="false">
                <input v-model="include_raw_exchanges" id="include_raw_exchanges" type="checkbox" class="form-check-input">
                <label for="include_raw_exchanges" class="form-check-label">include raw exchanges</label>
              </div>
               <div clas="form-check">
                <input name="screenshot" type="hidden" value="false">
                <input v-model="include_screenshot" id="include_screenshot" name="include_screenshot" type="checkbox" class="form-check-input">
                <label for="include_screenshot" class="form-check-label">include screenshot</label>
              </div>
              <div clas="form-check">
                <input name="include_pdf_snapshot" type="hidden" value="false">
                <input v-model="include_pdf_snapshot" id="include_pdf_snapshot" name="include_pdf_snapshot" type="checkbox" class="form-check-input">
                <label for="include_pdf_snapshot" class="form-check-label">include PDF snapshot</label>
              </div>
              <div clas="form-check">
                <input name="include_dom_snapshot" type="hidden" value="false">
                <input v-model="include_dom_snapshot" id="include_dom_snapshot" name="include_dom_snapshot" type="checkbox" class="form-check-input">
                <label for="include_dom_snapshot" class="form-check-label">include DOM snapshot</label>
              </div>
              <div clas="form-check">
                <input name="include_videos_as_attachment" type="hidden" value="false">
                <input v-model="include_videos_as_attachment" id="include_videos_as_attachment" name="include_videos_as_attachment" type="checkbox" class="form-check-input">
                <label for="include_videos_as_attachment" class="form-check-label">include videos as attachments</label>
              </div>
              <div clas="form-check">
                <input name="include_certificates_as_attachment" type="hidden" value="false">
                <input v-model="include_certificates_as_attachment" id="include_certificates_as_attachment" name="include_certificates_as_attachment" type="checkbox" class="form-check-input">
                <label for="include_certificates_as_attachment" class="form-check-label">include SSL certs as attachments</label>
              </div>
              <div clas="form-check">
                <input name="run_site_specific_behaviors" type="hidden" value="false">
                <input v-model="run_site_specific_behaviors" id="run_site_specific_behaviors" name="run_site_specific_behaviors" type="checkbox" class="form-check-input">
                <label for="run_site_specific_behaviors" class="form-check-label">run site-specific behaviors during capture</label>
              </div>
              <div clas="form-check">
                <input name="headless" type="hidden" value="false">
                <input v-model="headless" id="headless" name="headless" type="checkbox" class="form-check-input">
                <label for="headless" class="form-check-label">use a headless browser for capture</label>
              </div>
            </div>
          </div>
        </div>
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
    label: '',
    include_raw_exchanges: false,
    include_screenshot: true,
    include_pdf_snapshot: false,
    include_dom_snapshot: false,
    include_videos_as_attachment: true,
    include_certificates_as_attachment: true,
    run_site_specific_behaviors: true,
    headless: true,
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
        label: this.label,
        include_raw_exchanges: this.include_raw_exchanges,
        include_screenshot: this.include_screenshot,
        include_pdf_snapshot: this.include_pdf_snapshot,
        include_dom_snapshot: this.include_dom_snapshot,
        include_videos_as_attachment: this.include_videos_as_attachment,
        include_certificates_as_attachment: this.include_certificates_as_attachment,
        run_site_specific_behaviors: this.run_site_specific_behaviors,
        headless: this.headless,
        created_at: new Date().toISOString()
      })));
      this.requested_urls = '';
      this.label = '';
    }
  },
}
</script>

<style></style>
