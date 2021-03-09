<template>
<TheNavbar/>
<main>
  <TheMainHeader
    head="Create a new archive"
    subhead="Enter any URL to capture it in a downloadable archive."/>

  <div class="mt-5">
    <CaptureForm/>
  </div>

  <div class="mt-5">
    <CaptureList/>
  </div>
</main>
</template>

<script lang="ts">
import TheNavbar from './TheNavbar.vue'
import TheMainHeader from './TheMainHeader.vue'
import CaptureForm from './CaptureForm.vue'
import CaptureList from './CaptureList.vue'

export default {
  components: {
    TheNavbar,
    TheMainHeader,
    CaptureForm,
    CaptureList
  },
  mounted() {
    const replay = document.createElement('script')
    replay.setAttribute('src', 'https://cdn.jsdelivr.net/npm/replaywebpage@1.3.9/ui.js')
    document.head.appendChild(replay)
  }
}
</script>

<style scoped>
</style>
