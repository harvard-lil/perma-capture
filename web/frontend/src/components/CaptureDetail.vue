<template>
  <div class="capture-detail-container" v-if="displayedCapture">
    <div class="data-group">
      <span>Recorded {{ getDate(displayedCapture.created_at) }}</span>
      <span class="float-end" v-if="!isMobile">
      <a class="btn bi bi-download download-button" :href="downloadUrl"></a>
    </span>
    </div>
    <div class="data-group">
      <h3 class="h6">Submitted URL</h3>
      <a :href="displayedCapture.validated_url">{{ displayedCapture.requested_url }}</a>
    </div>
    <div class="data-group" v-if="displayedCapture.label">
      <h3 class="h6">Labels</h3>
      <p>{{ displayedCapture.label }}</p>
    </div>
    <div class="data-group">
      <div v-if="displayedCapture.message" class="contextItem">
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
  </div>
</template>

<script>
import {formatDate} from '../lib/helpers';

export default {
  name: "CaptureDetail",

  computed: {
    downloadUrl() {
      return this.displayedCapture.archive ? this.displayedCapture.archive.download_url : null
    },
    size() {
      return this.displayedCapture.archive ? Number((this.displayedCapture.archive.warc_size / (1024 * 1024)).toFixed(2)) : 0
    },
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
