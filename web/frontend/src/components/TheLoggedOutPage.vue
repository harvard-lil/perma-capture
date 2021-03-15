<template>
<TheMainHeader
  head="Logged out"/>
You have logged out.
<router-link :to="{name: 'login'}">Log in again</router-link>
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
