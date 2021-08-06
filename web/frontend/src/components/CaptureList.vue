<template>
  <div class="captures-list">
    <header class="captures-header">
      <h2 class="list-title">Capture history</h2>
    </header>
    <ul ref="captureList" :class="{'scrollable': scrollable, 'scrolled': scrolled}" @scroll="applyScrollStyles">
      <CaptureListItem
          v-for="capture in captures(sortBy, sortDesc)"
          :key="capture.id"
          :capture="capture"
      />
      <li v-if="loading" class="capture-list-loading">Loading...</li>
    </ul>
  </div>

</template>

<script lang="ts">
import CaptureListItem from './CaptureListItem.vue'

import {createNamespacedHelpers} from 'vuex'

const {mapGetters, mapActions, mapState} = createNamespacedHelpers('captures')

export default {
  poller: null,
  components: {
    CaptureListItem
  },
  data: () => ({
    loading: true,
    sortBy: 'created_at',
    sortDesc: true,
    headings: {
      status: 'Status',
      url: 'URL',
      label: 'Label',
      capture_oembed_view: 'Embedded Version',
      created_at: 'Created At'
    },
    scrollable: false,
    scrolled: false
  }),
  computed: {
    ...mapGetters({
      processing: 'processing',
      captures: 'sortedBy'
    }),
    ...mapState({
      apiContext: 'apiContext'
    }),
    apiParams() {
      return {ordering: (this.sortDesc ? '-' : '') + this.sortBy}
    }
  },
  methods: {
    ...mapActions([
      'list',
      'pageForward',
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
    clearLazyLoadListeners() {
      this.$refs.captureList.removeEventListener("scroll", this.handleLazyLoad);
      window.removeEventListener("scroll", this.handleLazyLoad);
    },
    handleLazyLoad(e) {
      console.log('scrolling!')
      let element = this.$refs.captureList;
      let scrolling_mobile_window = this.$store.getters.isSmallestScreen && element.getBoundingClientRect().bottom < window.innerHeight;
      let scrolling_capture_list = !this.$store.getters.isSmallestScreen && element.scrollHeight - Math.abs(element.scrollTop) === element.clientHeight;
      if (scrolling_mobile_window || scrolling_capture_list) {
        console.log('more!')
        this.clearLazyLoadListeners()
        this.loading = true
        this.pageForward().then(() => this.loading = false)
      }
    },
    checkIsScrollable() {
      this.$nextTick(function () {
        if (!this.$store.getters.isSmallestScreen && this.$refs.captureList.scrollHeight >= (0.8 * this.$store.getters.viewportHeight)){
          this.scrollable = true;
        } else {
          this.scrollable = false;
        }
      })
    },
    applyScrollStyles(e) {
      if (e.target.scrollTop > 0) {
        this.scrolled = true;
      } else {
        this.scrolled = false;
      }
    },
    changeSort(prop) {
      if (this.sortBy == prop) {
        this.sortDesc = !this.sortDesc
      } else {
        this.sortBy = prop
        this.sortDesc = true
      }
    }
  },
  watch: {
    apiParams: {
      deep: true,
      handler() {
        this.list(this.apiParams)
      }
    },
    apiContext: {
      deep: true,
      handler(current, previous) {
        if (current.next) {
          // Don't bother tracking whether it's already been attached
          // https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener#multiple_identical_event_listeners
          this.$refs.captureList.addEventListener("scroll", this.handleLazyLoad);
          window.addEventListener("scroll", this.handleLazyLoad)
        } else {
          this.clearLazyLoadListeners()
        }
      }
    },
    processing(current, previous) {
      if (this.$options.poller) {
        if (!current.length) this.clearProcessingPoll()
      } else if (current.length) {
        this.pollForProcessingChanges()
      }
    }
  },
  created() {
    this.list().then(() => this.loading = false)
  },
  mounted() {
    this.$nextTick(function () {
      window.addEventListener('resize', this.checkIsScrollable);
    })
  },
  updated() {
    this.$nextTick(function () {
      this.checkIsScrollable()
    })
  },
  beforeUnmount() {
    this.clearProcessingPoll();
    this.clearLazyLoadListeners();
    window.removeEventListener('resize', this.checkIsScrollable);
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
