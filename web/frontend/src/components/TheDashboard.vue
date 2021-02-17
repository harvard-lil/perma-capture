<template>
<TheHeader/>
<main class="container wrapper-flex">
  <div class="row">
    <h1 class="h1">Create a new archive</h1>
    <p class="subheading">Enter any URL to capture it in a downloadable archive.</p>
    <CaptureForm/>
  </div>
</main>
</template>

<script lang="ts">
import TheHeader from './TheHeader.vue'
import CaptureForm from './CaptureForm.vue'

export default {
  components: {
      TheHeader,
      CaptureForm
  }
}
</script>

<style scoped>
.h1 {
  font-size: 50px;
}
</style>
