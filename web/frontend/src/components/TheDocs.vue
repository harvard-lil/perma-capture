<template>
<TheNavbar/>
</template>

<script lang="ts">
import TheNavbar from './TheNavbar.vue'

export default {
  components: {
    TheNavbar
  }
}
</script>

<style>
/* Fixes overflow: auto not working on code blocks */
.col {
  min-width: 0
}

h2:not(:first-child) {
  margin-top: 3rem;
}
h3 {
  margin-top: 2rem;
}
h4 {
  margin-top: 1.5rem;
}

pre {
  padding: 1rem;
  background-color: var(--color-background);
}
</style>
