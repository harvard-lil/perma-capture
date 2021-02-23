<template>
<nav class="navbar mb-3 py-3">
  <a href="/" class="navbar-brand">{{ app_name }}</a>
  <TheMainNav/>
</nav>
</template>

<script lang="ts">
import TheMainNav from './TheMainNav.vue'
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('globals')

export default {
  components: {
    TheMainNav
  },
  computed: mapState([
    'app_name'
  ])
}
</script>

<style scoped>
  .navbar-brand {
    color: var(--color-black);
  }
</style>
