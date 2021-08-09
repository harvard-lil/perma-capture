<template>
  <TheNavbar/>
  <main>
    <router-view/>
  </main>
  <TheFooter/>
</template>

<script lang="ts">
import '@popperjs/core'
import 'bootstrap'

import {defineComponent} from 'vue'
import TheNavbar from './components/TheNavbar.vue'
import TheFooter from './components/TheFooter.vue'

export default defineComponent({
  name: 'App',
  components: {
    TheNavbar,
    TheFooter
  }
})
</script>

<style lang="scss">
@import "styles/styles";
</style>
