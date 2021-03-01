<template>
<table class="table">
  <thead>
    <tr>
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
const { mapGetters, mapActions } = createNamespacedHelpers('captures')

export default {
  poller: null,
  components: {
    CaptureListItem
  },
  computed: {
    ...mapGetters({
      captures: 'createdAtDesc',
      processing: 'processing'
    })
  },
  methods: {
    ...mapActions([
      'list',
      'batchRead'
    ]),
    pollForProcessingChanges() {
      this.$options.poller = setInterval(() => {
        this.batchRead(this.processing)
      }, 3000)
    },
    clearProcessingPoll() {
      clearInterval(this.$options.poller)
    }
  },
  watch: {
    processing(current, previous) {
      if(this.$options.poller){
        if(!current.length) this.clearProcessingPoll()
      } else if(current.length) {
        this.pollForProcessingChanges()
      }
    }
  },
  created() {
    this.list()
  },
  unmounted() {
    this.clearProcessingPoll()
  }
}
</script>

<style scoped>
</style>
