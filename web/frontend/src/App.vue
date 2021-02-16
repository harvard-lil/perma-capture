<template>
  <TheDashboard/>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import TheDashboard from './components/TheDashboard.vue'

export default defineComponent({
  name: 'App',
  components: {
    TheDashboard
  }
})
</script>

<style>
@import 'normalize.css';
@import '@fontsource/roboto/300.css';
@import '@fontsource/roboto/400.css';
@import '@fontsource/roboto/900.css';

html, body {
  height: 100%;
  background-color: #F6F8F1;
  font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: #2D76EE;
}
</style>
