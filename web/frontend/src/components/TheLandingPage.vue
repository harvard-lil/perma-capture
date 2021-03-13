<template>
<TheMainHeader
  :head="app_name"
  subhead="A Witness Server & Suite of Tools for Journalists and Fact Checkers"/>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('globals')

import TheMainHeader from './TheMainHeader.vue'

export default {
  components: {
    TheMainHeader
  },
  computed: mapState([
    'app_name'
  ])
}
</script>

<style scoped>
</style>
