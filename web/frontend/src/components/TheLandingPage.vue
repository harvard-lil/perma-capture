<template>
<TheNavbar/>
<main>
  <TheMainHeader
    :head="app_name"
    subhead="A Witness Server & Suite of Tools for Journalists and Fact Checkers"/>
</main>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('globals')

import TheNavbar from './TheNavbar.vue'
import TheMainHeader from './TheMainHeader.vue'

export default {
  components: {
    TheNavbar,
    TheMainHeader
  },
  computed: mapState([
    'app_name'
  ])
}
</script>

<style scoped>
</style>
