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
  font-size: 100%;
  background-color: #F6F8F1;
  font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: #2D76EE;
}

h1 {
  font-weight: 700;
  color: black;
}

.wrapper {
  height:100%;
  text-align: center;
}

.wrapper-flex {
  display: -webkit-flex;
  display: flex;
  flex-direction: column;
  -webkit-justify-content: center;
  justify-content:center;
}

.subheading {
  text-align: center;
  margin-top: -32px;
  color: #DD671A;
  font-weight: bold;
  font-size: 1.5em;
  line-height: 1.3;
}
</style>
