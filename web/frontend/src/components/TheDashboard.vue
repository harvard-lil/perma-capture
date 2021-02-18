<template>
<TheNavbar/>
<main>
  <h1 class="text-center display-5">Create a new archive</h1>
  <p class="text-center">Enter any URL to capture it in a downloadable archive.</p>
  <CaptureForm/>
</main>
</template>

<script lang="ts">
import TheNavbar from './TheNavbar.vue'
import CaptureForm from './CaptureForm.vue'

export default {
  components: {
      TheNavbar,
      CaptureForm
  }
}
</script>

<style scoped>
</style>
