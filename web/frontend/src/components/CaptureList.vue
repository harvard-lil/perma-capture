<template>
<table class="table">
  <thead>
    <tr>
      <th v-for="(heading, prop) in headings" scope="col">
        <a @click="changeSort(prop)" role="button" :class="sortBy == prop ? 'active' : ''" class="sortButton">
          {{ heading }}
          <span :class="`bi-sort-${sortDesc ? 'down' : 'up'}`" class="sortIcon bi"></span>
        </a>
      </th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    <CaptureListItem
      v-for="capture in captures(sortBy, sortDesc)"
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
  data: () => ({
    sortBy: 'created_at',
    sortDesc: true,
    headings: {
      status: 'Status',
      requested_url: 'URL',
      label: 'Label',
      capture_oembed_view: 'Embedded Version',
      created_at: 'Created At'
    }
  }),
  computed: {
    ...mapGetters({
      captures: 'sortBy',
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
    },
    changeSort(prop) {
      if(this.sortBy == prop){
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = prop
        this.sortDesc = true
      }
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
.sortIcon {
  visibility: hidden;
}
.sortButton:hover .sortIcon,
.active .sortIcon {
  visibility: visible;
}

.sortButton:hover .sortIcon {
  opacity: 0.25;
}
.active .sortIcon,
.active:hover .sortIcon {
  opacity: 1;
}
.sortButton {
  color: inherit;
  text-decoration: none;
  padding: 0.5rem;
  margin-left: -0.5rem;
}
.sortButton:hover,
.sortButton.active {
  background: var(--color-background);
  color: #000;
}
</style>
