<template>
  <li :class="{'active': !(hasFailed || isProcessing) && active, 'details-shown': displayContext}" class="capture-list-item">
    <div class="favicon">🔗</div>
    <h6 class="capture-title">Lorem Ipsum title</h6>
    <div class="btn-group" v-if="downloadUrl">
      <span v-if="isProcessing"
            class="status-icon spinner spinner-border spinner-border-sm"
            role="status" aria-hidden="true">
      </span>
      <span v-else-if="hasFailed" class="status-icon bi bi-x"> </span>

      <!--  on success  -->
      <template v-else>
        <span class="status-icon bi bi-check"></span>
        <a role="button" class="btn btn-primary bi bi-download download-button" :href="downloadUrl"></a>
        <a role="button" class="btn bi bi-chevron-right replay-toggle" :class="{active: displayContext}"
           @click="toggleCaptureDetails(capture)"></a>
      </template>
    </div>

    <a class="capture-url" :href="url">{{ url }}</a>
    <!--    <label>{{ capture.label }}</label>-->
    <!--      <td><input class="form-check-input" type="checkbox" v-model="capture.capture_oembed_view" id="flexCheckDisabled"-->
    <!--               disabled></td>-->
    <span class="secondary-text recorded-date">Recorded {{ getDate(capture.created_at) }}</span>&nbsp;
    <span v-if="active" class="warning-text expired-date">Expires in {{ getDate(capture.capture_end_time) }}</span>
    <span v-else class="expired-date">Expired</span>
    <br/>
    <!--    <a v-if="capture.message" role="button" class="btn btn-primary bi bi-question-diamond"-->
    <!--       @click="toggleCaptureDetails(capture)"></a>-->

    <template v-if="isMobile && displayContext && $store.getters.capture">
      <capture-detail v-if="capture.id === $store.getters.capture.id" :capture="capture"/>
    </template>
  </li>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapActions} = createNamespacedHelpers('captures')

import {TransitionalStates, FailureStates, SuccessStates} from '../constants/captures'
import {snakeToPascal} from '../lib/helpers'
import store from '../store/index.ts';
import CaptureDetail from './CaptureDetail.vue'
import {formatDate} from '../lib/helpers';

export default {
  components: {
    CaptureDetail
  },
  props: ['capture'],
  data: () => ({
    displayContext: false,
  }),
  computed: {
    statusOrDefault() {
      return this.capture.status || 'pending'
    },
    isProcessing() {
      return snakeToPascal(this.statusOrDefault) in TransitionalStates
    },
    hasFailed() {
      return snakeToPascal(this.statusOrDefault) in FailureStates
    },
    url() {
      return this.capture.validated_url || this.capture.requested_url
    },
    active() {
      let duration = new Date(this.capture.capture_end_time) - new Date(this.capture.created_at);
      if (duration <= 0) return;
      return true;
    },
    isMobile() {
      return this.$store.getters.isMobile;
    },
    statusBG() {
      return {
        invalid: "danger",
        pending: "secondary",
        in_progress: "primary",
        completed: "success",
        failed: "danger"
      }[this.statusOrDefault]
    },
    downloadUrl() {
      return this.capture.archive ? this.capture.archive.download_url : null
    },
  },
  methods: {
    ...mapActions(['read']),
    toggleCaptureDetails(capture) {
      this.displayContext = !this.displayContext
      // set this as capture if toggling to show capture
      this.displayContext ? store.commit('setCapture', capture) : store.commit('setCapture', undefined)
    },
    getDate(date) {
      return formatDate(date);
    }
  },
}
</script>
