<template>
<nav class="navbar mb-3 py-3">
  <a href="/" class="navbar-brand">{{ app_name }}</a>
  <div class="dropdown">
    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton1" data-bs-toggle="dropdown" aria-expanded="false"></button>
    <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton1">
      <li>
        Things
      </li>
    </ul>
  </div>
</nav>
</template>

<script lang="ts">
import TheMainNav from './TheMainNav.vue'
import { mapState } from 'vuex'

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
</style>
