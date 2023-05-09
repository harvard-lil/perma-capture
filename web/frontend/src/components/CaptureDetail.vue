<template>
  <div class="capture-detail-container" v-if="displayedCapture">
    <div v-if="isMobile" class="data-group">
      <span>Submitted {{ getDate(displayedCapture.created_at) }}</span><br>
      <span v-if="getArchiveAttribute('download_url')">Expires {{ getDate(expiresAt) }}</span>
      <span v-else-if="succeeded">Expired {{ getDate(expiresAt) }}</span>
    </div>
    <div v-else class="data-group download-button-group">
      <span class="float-end">
        <a v-if="getArchiveAttribute('download_url')" class="btn bi bi-download download-button" :href="getArchiveAttribute('download_url')"></a>
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
    <div v-if="getArchiveAttribute('screenshot_url') && !getArchiveAttribute('download_url')" class="data-group">
      <h3 class="h6">Screenshot</h3>
      <img class="screenshot" :src="getArchiveAttribute('screenshot_url')">
    </div>
    <div v-if="getArchiveAttribute('download_url')" class="data-group">
      <h3 class="h6">Replay</h3>
      <div class="iframe-container">
        <replay-web-page :source="getArchiveAttribute('download_url')"
                         :url="displayedCapture.validated_url"
                         replaybase="/replay/"
                         class="replay contextItem"/>
      </div>
    </div>
    <div v-if="size" class="data-group">
      <h3 class="h6">Capture size</h3>
      <p>{{ size }}MB</p>
    </div>
    <div v-if="getArchiveAttribute('title')" class="data-group">
      <h3 class="h6">Title</h3>
      <p>{{ getArchiveAttribute('title')  }}</p>
    </div>
    <div v-if="getArchiveAttribute('description')" class="data-group">
      <h3 class="h6">Description</h3>
      <p>{{ getArchiveAttribute('description') }}</p>
    </div>
    <div v-if="getArchiveAttribute('target_url_content_type')" class="data-group">
      <h3 class="h6">Content Type</h3>
      <p>{{ getArchiveAttribute('target_url_content_type') }}</p>
    </div>
    <div v-if="getArchiveAttribute('summary')" class="data-group">
      <h3 class="h6">Summary</h3>
      <pre>{{ getArchiveAttribute('summary') }}</pre>
    </div>
  </div>
</template>

<script>
import {formatDate, snakeToPascal} from '../lib/helpers';
import {SuccessStates} from '../constants/captures'

export default {
  name: "CaptureDetail",

  computed: {
    size() {
      return this.displayedCapture.archive ? Number((this.displayedCapture.archive.size / (1024 * 1024)).toFixed(2)) : 0
    },
    expiresAt() {
      return this.displayedCapture.archive ? new Date(this.displayedCapture.archive.download_expiration_timestamp) : null
    },
    succeeded() {
      return snakeToPascal(this.displayedCapture.status || 'pending') in SuccessStates
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
    getArchiveAttribute(attribute) {
      return this.displayedCapture?.archive[attribute]
    }
  }
}
</script>
