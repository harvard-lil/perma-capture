<template>
<nav class="navbar navbar-expand-lg mb-3 py-3">
  <div class="container-fluid">
    <router-link :to="{name: 'root'}" class="navbar-brand">{{ app_name }}</router-link>
    <TheMainNav/>
  </div>
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
