<template>
<h1 :class="{'text-center': center}" class="main-header">{{ head }}</h1>
<p :class="{'text-center': center}" class="main-subheader" v-if="subhead">{{ subhead }}</p>
</template>

<script lang="ts">
export default {
  props: {
    head: {type: String},
    subhead: {type: String},
    center: {type: Boolean, default: true}
  }
}
</script>

<style scoped>
</style>
