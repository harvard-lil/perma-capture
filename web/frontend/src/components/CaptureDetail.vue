<template>
  <div class="capture-detail-container">
    capture is shown!!!
    {{ capture }}
  </div>
  <div>
    {{ capture }}
    <div v-if="capture.message" class="contextItem">
      <div class="alert alert-danger">{{ capture.message }}</div>
    </div>
<!--      <replay-web-page v-if="downloadUrl"-->
<!--                       :source="downloadUrl"-->
<!--                       :url="url"-->
<!--                       replaybase="/replay/"-->
<!--                       class="replay contextItem"/>-->
  </div>
</template>

<script>
export default {
  name: "CaptureDetail",
  props: ["capture"],

  data() {
    return {}
  },
  mounted() {
    console.log('CaptureDetail', this.capture)
  }
}
</script>

<style scoped>

</style>