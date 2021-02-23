<template>
  <TheDashboard/>
</template>

<script lang="ts">
import '@popperjs/core'
import 'bootstrap'

import { defineComponent } from 'vue'
import TheDashboard from './components/TheDashboard.vue'

export default defineComponent({
  name: 'App',
  components: {
    TheDashboard
  }
})
</script>

<style lang="scss">
@import "styles/_vars-global-native";
@import "styles/_bootstrap";

@import "@fontsource/roboto/300";
@import "@fontsource/roboto/400";
@import "@fontsource/roboto/900";

html, body {
  font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
}
</style>
