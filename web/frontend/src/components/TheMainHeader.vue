<template>
<h1 class="text-center display-5">{{ head }}</h1>
<p class="text-center" v-if="subhead">{{ subhead }}</p>
</template>

<script lang="ts">
export default {
  props: [
    'head',
    'subhead'
  ]
}
</script>

<style scoped>
</style>
