<template>
  <div class="capture-detail-container">
    <h6>Recorded {{ capture.created_at }} </h6>
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
export default {
  name: "CaptureDetail",
  props: ["capture"],
  computed: {
    downloadUrl() {
      return this.capture.archive ? this.capture.archive.download_url : null
    },
  },
}
</script>

<style scoped>

</style>