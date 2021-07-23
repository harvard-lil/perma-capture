<template>
  <div class="capture-detail-container">
    <div class="data-group">
      <span>Recorded {{ getDate(capture.created_at) }}</span>
      <span class="float-end" v-if="!isMobile">
      <a role="button" class="btn bi bi-download download-button" :href="downloadUrl"></a>
    </span>
    </div>
    <div class="data-group">
      <h6>Submitted URL</h6>
      <a :href="capture.validated_url">{{ capture.requested_url }}</a>
    </div>
    <div class="data-group">
      <div v-if="capture.message" class="contextItem">
        <div class="alert alert-danger">{{ capture.message }}</div>
      </div>
    </div>
    <div class="data-group">
      <h6>Preview</h6>
      <div class="iframe-container">
        <replay-web-page v-if="downloadUrl"
                         :source="downloadUrl"
                         :url="capture.url"
                         replaybase="/replay/"
                         class="replay contextItem"/>
      </div>
    </div>
    <div class="data-group">
      <h6>Capture size</h6>
      <p>{{ size }}MB</p>
    </div>
  </div>
</template>

<script>
import {formatDate} from '../lib/helpers';

export default {
  name: "CaptureDetail",
  props: ["capture"],

  computed: {
    downloadUrl() {
      return this.capture.archive ? this.capture.archive.download_url : null
    },
    size() {
      return Number((this.capture.archive.warc_size / (1024 * 1024)).toFixed(2))
    },
    isMobile() {
      return this.$store.getters.isMobile;
    },
  },
  methods: {
    getDate(date) {
      return formatDate(date);
    },

  }
}
</script>
