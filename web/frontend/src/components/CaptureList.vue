<template>
<table class="table">
  <thead>
    <tr>
      <th scope="col">ID</th>
      <th scope="col">URL</th>
      <th scope="col">Status</th>
      <th scope="col">Created At</th>
    </tr>
  </thead>
  <tbody>
    <CaptureListItem
      v-for="capture in captures"
      :key="capture.id"
      :capture="capture"
      />
  </tbody>
</table>
</template>

<script lang="ts">
import CaptureListItem from './CaptureListItem.vue'
import { mapState, mapActions } from 'vuex'

export default {
  components: {
    CaptureListItem
  },
  computed: mapState({
    captures: state => state.captures.all
  }),
  created () {
    this.$store.dispatch('captures/list')
  }
}
</script>

<style scoped>
</style>
