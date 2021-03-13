<template>
<TheNavbar/>
<main>
<router-view />
</main>
</template>

<script lang="ts">
import '@popperjs/core'
import 'bootstrap'

import { defineComponent } from 'vue'
import TheNavbar from './components/TheNavbar.vue'

export default defineComponent({
  name: 'App',
  components: {
    TheNavbar
  }
})
</script>

<style lang="scss">
@import "styles/_vars-global-native";
@import "styles/_bootstrap";
@import "bootstrap-icons/font/bootstrap-icons";

@import "@fontsource/roboto/300";
@import "@fontsource/roboto/400";
@import "@fontsource/roboto/900";

html, body {
  font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
}
</style>
