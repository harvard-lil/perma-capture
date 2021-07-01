<template>
<TheMainHeader
  head="Create a new archive"
  subhead="Enter any URL to capture it in a downloadable archive."/>

<div class="mt-5">
  <CaptureForm/>
</div>

<div class="mt-5">
  <CaptureList/>
</div>
</template>

<script lang="ts">
import TheMainHeader from './TheMainHeader.vue'
import CaptureForm from './CaptureForm.vue'
import CaptureList from './CaptureList.vue'

export default {
  components: {
    TheMainHeader,
    CaptureForm,
    CaptureList
  },
  mounted() {
    // const replay = document.createElement('script')
    // replay.setAttribute('src', 'https://cdn.jsdelivr.net/npm/replaywebpage@1.3.9/ui.js')
    // document.head.appendChild(replay)

    this.$nextTick(() => {
      window.addEventListener('resize', debounce(() => {
            this.$store.commit('setWindowWidth')
          }, 250)
      );
    });

  }
}
</script>

<style scoped>
</style>
