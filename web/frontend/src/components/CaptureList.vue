<template>
<table class="table">
  <thead>
    <tr>
      <th scope="col">ID</th>
      <th scope="col">URL</th>
      <th scope="col">Label</th>
      <th scope="col">Embedded Version</th>
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

import { createNamespacedHelpers } from 'vuex'
const { mapState, mapActions } = createNamespacedHelpers('captures')

export default {
  components: {
    CaptureListItem
  },
  computed: {
    ...mapState({
      captures: state => state.all.sort((a, b) => b.id - a.id)
    })
  },
  methods: {
    ...mapActions(['list'])
  },
  created () {
    this.list()
  }
}
</script>

<style scoped>
</style>
