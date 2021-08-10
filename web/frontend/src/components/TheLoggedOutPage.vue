<template>
<TheMainHeader
  head="Logged out"/>
<div class="container text-center">
  <div>You have logged out.</div>
  <div><router-link :to="{name: 'login'}">Log in again</router-link></div>
</div>
</template>

<script lang="ts">
import TheMainHeader from './TheMainHeader.vue'

export default {
  components: {
    TheMainHeader
  }
}
</script>

<style>
</style>
