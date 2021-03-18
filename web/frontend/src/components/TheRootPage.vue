<template>
<TheDashboard v-if="is_authenticated"/>
<TheLandingPage v-else/>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('user')

import TheLandingPage from './TheLandingPage.vue'
import TheDashboard from './TheDashboard.vue'

export default {
  components: {
    TheLandingPage,
    TheDashboard
  },
  computed: mapState([
    'is_authenticated'
  ])
}
</script>

<style scoped>
</style>
