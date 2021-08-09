<template>
  <li :class="{'active': (isProcessing || downloadUrl), 'details-shown': displayDetails}"
      class="capture-list-item">
    <div class="content">
      <div class="favicon" aria-hidden="true">🔗</div>
      <h3 class="h6 capture-title">{{ title }}</h3>
      <div class="btn-group spinner">
        <span v-if="isProcessing"
              class="status-icon spinner spinner-border spinner-border-sm"
              aria-hidden="true">
        </span>
        <template v-else>
          <a v-if="downloadUrl" class="btn bi bi-download download-button" :href="downloadUrl"></a>
          <span v-else class="btn bi bi-download download-button placeholder"></span>
          <button class="btn bi bi-chevron-right replay-toggle" :class="{active: displayDetails}"
             @click="toggleCaptureDetails(capture)"></button>
        </template>
      </div>
      <span v-if="statusOrDefault==='Invalid'"  class="capture-url" v-text="shortenUrl(url)"></span>
      <span v-else class="capture-url"><a :href="url" v-text="shortenUrl(url)"></a></span>
      <span class="secondary-text recorded-date">Submitted {{ getDate(capture.created_at) }}</span>&nbsp;
      <template v-if="!isProcessing">
        <span v-if="downloadUrl" class="warning-text expired-date">Expires {{ getDate(expiresAt) }}</span>
        <span v-else-if="succeeded" class="expired-date">Expired {{ getDate(expiresAt) }}</span>
      </template>
      <template v-if="isMobile && displayDetails && capture.id === $store.getters.displayedCapture.id">
        <capture-detail/>
      </template>
    </div>
  </li>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'
import {SuccessStates, FailureStates, TransitionalStates} from '../constants/captures'
import {formatDate, snakeToPascal} from '../lib/helpers'
import store from '../store/index.ts';
import CaptureDetail from './CaptureDetail.vue'

const {mapActions} = createNamespacedHelpers('captures')

export default {
  components: {
    CaptureDetail
  },
  props: ['capture'],
  data: () => ({
    displayDetails: false,
  }),
  computed: {
    statusOrDefault() {
      return snakeToPascal(this.capture.status || 'pending')
    },
    isProcessing() {
      return this.statusOrDefault in TransitionalStates
    },
    succeeded() {
      return this.statusOrDefault in SuccessStates
    },
    hasFailed() {
      return this.statusOrDefault in FailureStates
    },
    title() {
      let title;
      switch(this.statusOrDefault) {
        case 'Invalid':
          title = 'Invalid URL';
          break;
        case 'InProgress':
          title = 'Capture In Progress';
          break;
        case 'Failed':
          title = 'Capture Failed';
          break;
        case 'Completed':
          title = 'Lorem Ipsum title';
          break;
        default:
          title = 'Capture Pending';
      }
      return title
    },
    url() {
      return this.capture.validated_url || this.capture.requested_url
    },
    downloadUrl() {
      return this.capture.archive ? this.capture.archive.download_url : null
    },
    expiresAt() {
      return this.capture.archive ? new Date(this.capture.archive.download_expiration_timestamp) : null
    },
    isMobile() {
      return this.$store.getters.isMobile;
    }
  },
  watch: {
    '$store.getters.displayedCapture': function (newcapture) {
      if (!(newcapture) || newcapture.id !== this.capture.id) {
        this.displayDetails = false;
      }
    }
  },
  methods: {
    ...mapActions(['read']),
    toggleCaptureDetails(capture) {
      this.displayDetails = !this.displayDetails
      this.displayDetails ? store.commit('setDisplayedCapture', capture) : store.commit('setDisplayedCapture', undefined)
    },
    getDate(date) {
      return formatDate(date);
    },
    shortenUrl(url) {
      if (url.length <= 100) return url
      return url.slice(0, 100) + '...';
    },
  },
}
</script>
