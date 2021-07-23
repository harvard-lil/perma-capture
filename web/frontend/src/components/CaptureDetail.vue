<template>
  <div class="capture-detail-container">
    <h6>Recorded {{ getDate(capture.created_at) }} </h6>
    <h3>{{ capture.requested_url }}</h3>
    <div v-if="capture.message" class="contextItem">
      <div class="alert alert-danger">{{ capture.message }}</div>
    </div>
    <div class="iframe-container">
      <replay-web-page v-if="downloadUrl"
                       :source="downloadUrl"
                       :url="capture.url"
                       replaybase="/replay/"
                       class="replay contextItem"/>
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
  },
  methods: {
    getDate(date) {
      return formatDate(date);
    }
  }
}
</script>

<style scoped>

</style>