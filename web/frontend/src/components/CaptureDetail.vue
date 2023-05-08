<template>
  <div class="capture-detail-container" v-if="displayedCapture">
    <div v-if="isMobile" class="data-group">
      <span>Submitted {{ getDate(displayedCapture.created_at) }}</span><br>
      <span v-if="downloadUrl">Expires {{ getDate(expiresAt) }}</span>
      <span v-else-if="succeeded">Expired {{ getDate(expiresAt) }}</span>
    </div>
    <div v-else class="data-group download-button-group">
      <span class="float-end">
        <a v-if="downloadUrl" class="btn bi bi-download download-button" :href="downloadUrl"></a>
      </span>
    </div>
    <div class="data-group">
      <h3 class="h6">Requested URL</h3>
      <a :href="displayedCapture.validated_url">{{ displayedCapture.requested_url }}</a>
    </div>
    <div class="data-group" v-if="displayedCapture.label">
      <h3 class="h6">Labels</h3>
      <p>{{ displayedCapture.label }}</p>
    </div>
    <div v-if="displayedCapture.message" class="data-group">
      <h3 class="h6">Error Message</h3>
      <div  class="contextItem">
        <div class="alert alert-danger">{{ displayedCapture.message }}</div>
      </div>
    </div>
    <div v-if="downloadUrl" class="data-group">
      <h3 class="h6">Preview</h3>
      <div class="iframe-container">
        <replay-web-page :source="downloadUrl"
                         :url="displayedCapture.validated_url"
                         replaybase="/replay/"
                         class="replay contextItem"/>
      </div>
    </div>
    <div v-if="size" class="data-group">
      <h3 class="h6">Capture size</h3>
      <p>{{ size }}MB</p>
    </div>
    <div v-if="summary" class="data-group">
      <h3 class="h6">Summary</h3>
      <pre>{{ summary }}</pre>
    </div>
  </div>
</template>

<script>
import {formatDate, snakeToPascal} from '../lib/helpers';
import {SuccessStates} from '../constants/captures'

export default {
  name: "CaptureDetail",

  computed: {
    downloadUrl() {
      return this.displayedCapture.archive ? this.displayedCapture.archive.download_url : null
    },
    size() {
      return this.displayedCapture.archive ? Number((this.displayedCapture.archive.warc_size / (1024 * 1024)).toFixed(2)) : 0
    },
    expiresAt() {
      return this.displayedCapture.archive ? new Date(this.displayedCapture.archive.download_expiration_timestamp) : null
    },
    succeeded() {
      return snakeToPascal(this.displayedCapture.status || 'pending') in SuccessStates
    },
    summary() {
      return this.displayedCapture.archive ? this.displayedCapture.archive.summary : null
    },
    isMobile() {
      return this.$store.getters.isMobile;
    },
    displayedCapture() {
      return this.$store.getters.displayedCapture;
    }
  },
  methods: {
    getDate(date) {
      return formatDate(date);
    },
  }
}
</script>
