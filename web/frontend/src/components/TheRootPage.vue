<template>
  <div class="container-full root-page-container">
    <TheDashboard v-if="is_authenticated"/>
  </div>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapState} = createNamespacedHelpers('user')

import TheDashboard from './TheDashboard.vue'

export default {
  components: {
    TheDashboard
  },
  computed: mapState([
    'is_authenticated'
  ]),
  beforeMount() {
    // redirect to login if not logged in
    if (!(this.is_authenticated)) {
      this.$router.push('/user/login/')
    }
  }
}
</script>
