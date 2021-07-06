<template>
  <li>
    <!--    <span class="status badge" :class="`bg-${statusBG}`">-->
    <!--      <span v-if="isProcessing" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>-->
    <!--      <span v-else-if="hasFailed" class="bi bi-x"></span>-->
    <!--      <span v-else class="bi bi-check"></span>-->
    <!--    </span>-->
    <p class="capture-url"><a :href="url">{{ url }}</a></p>
    <!--    <label>{{ capture.label }}</label>-->
    <!--      <td><input class="form-check-input" type="checkbox" v-model="capture.capture_oembed_view" id="flexCheckDisabled"-->
    <!--               disabled></td>-->
    <span class="secondary-text">Recorded {{ formattedCaptureDate }}</span>&nbsp;
    <span v-if="formattedEndDate" class="warning-text">Expires in {{ formattedEndDate }}</span>
    <span v-else>Expired</span>
    <br/>
    <template v-if="downloadUrl">
      <a role="button" class="btn btn-primary bi bi-download mx-1" :href="downloadUrl"></a>
      <a role="button" class="btn btn-primary bi bi-chevron-up mx-1 replayToggle" :class="{active: displayContext}"
         @click="toggleCaptureDetails(capture)"></a>
    </template>
    <a v-if="capture.message" role="button" class="btn btn-primary bi bi-question-diamond mx-1"
       @click="toggleCaptureDetails(capture)"></a>

    <template v-if="$store.getters.isMobile && displayContext && $store.getters.capture">
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
    formattedCaptureDate() {
      let options = {year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric'};
      return (new Date(this.capture.created_at)).toLocaleDateString("en-US", options)
    },
    formattedEndDate() {
      let duration = new Date(this.capture.capture_end_time) - new Date(this.capture.created_at);
      if (duration <= 0) return;
      let minutes = Math.floor((duration / (1000 * 60)) % 60),
          hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
      if (hours) {
        return hours + ' hours and ' + minutes + ' minutes'
      } else if (minutes) {
        return minutes + ' minutes';
      }
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
    }
  },

}
</script>

<style scoped>
.status {
  font-size: 1em;
}

.contextItem {
  display: block;
  overflow: hidden;
  max-height: 200px;
}

.replay {
  min-height: 500px;
  height: 75vh;
}

.replayToggle.active::before {
  transform: rotate(180deg);
}

/* Without setting the transition timing on the parent, Vue will not add transition states for the child elements to use */
.slide-enter-active,
.slide-leave-active,
.slide-enter-active .contextItem,
.slide-leave-active .contextItem,
.replayToggle::before {
  transition: all 0.2s;
}

.slide-enter-from .contextItem,
.slide-leave-to .contextItem {
  height: 0;
  min-height: 0;
  max-height: 0;
}
</style>
