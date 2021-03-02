<template>
<TheNavbar/>
<main>
  <div class="mb-5">
    <h1 class="text-center display-5">Create a new archive</h1>
    <p class="text-center">Enter any URL to capture it in a downloadable archive.</p>
  </div>
  <div class="mb-5">
    <CaptureForm/>
  </div>
  <div class="mb-5">
    <CaptureList/>
  </div>
</main>
</template>

<script lang="ts">
import TheNavbar from './TheNavbar.vue'
import CaptureForm from './CaptureForm.vue'
import CaptureList from './CaptureList.vue'

export default {
  components: {
    TheNavbar,
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
