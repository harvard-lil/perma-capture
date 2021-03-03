<template>
<tr>
  <td>
    <span class="status badge" :class="`bg-${statusBG}`">
      <span v-if="isProcessing" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      <span v-else-if="hasFailed" class="bi bi-x"></span>
      <span v-else class="bi bi-check"></span>
    </span>
  </td>
  <td><a :href=capture.requested_url>{{ capture.requested_url }}</a></td>
  <td>{{ capture.label || '-' }}</td>
  <td><input class="form-check-input" type="checkbox" v-model="capture.capture_oembed_view" id="flexCheckDisabled" disabled></td>
  <td>{{ formattedDate }}</td>
  <td>
    <template v-if="downloadUrl">
      <a role="button" class="btn btn-primary bi bi-download mx-1" :href="downloadUrl"></a>
      <a role="button" class="btn btn-primary bi bi-chevron-up mx-1 replayToggle" :class="{active: displayReplay}" @click="toggleReplay"></a>
    </template>
  </td>
</tr>
<transition name="slide">
  <tr v-if="downloadUrl && displayReplay" class="replayRow">
    <td colspan="999" class="replayCell">
      <replay-web-page
        :source="downloadUrl"
        :url="capture.requested_url"
        replaybase="/vite/src/config/"
        class="replay"/>
    </td>
  </tr>
</transition>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('captures')

import { TransitionalStates, FailureStates, SuccessStates } from '../constants/captures'
import { snakeToPascal } from '../lib/helpers'

export default {
  props: ['capture'],
  data: () => ({
    displayReplay: false
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
    formattedDate() {
      return (new Date(this.capture.created_at)).toLocaleDateString()
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
    }
  },
  methods: {
    ...mapActions(['read']),
    toggleReplay() {
      this.displayReplay = !this.displayReplay
    }
  }
}
</script>

<style scoped>
.status {
  font-size: 1em;
}
.replayCell {
  padding: 0;
}
.replay {
  display: block;
  min-height: 500px;
  height: 75vh;
}

.replayToggle.active::before {
  transform: rotate(180deg);
}

/* Without setting the transition timing on the parent, Vue will not add transition states for the child elements to use */
.slide-enter-active,
.slide-leave-active,
.slide-enter-active .replay,
.slide-leave-active .replay,
.replayToggle::before {
  transition: all 0.2s;
}

.slide-enter-from .replay,
.slide-leave-to .replay {
  height: 0;
  min-height: 0;
}
</style>
