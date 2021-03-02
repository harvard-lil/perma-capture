<template>
<tr>
  <td>
    <span :class="['status', 'badge', `bg-${statusBG}`]">
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
      <a role="button" class="btn btn-primary bi bi-chevron-up mx-1"></a>
    </template>
  </td>
</tr>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('captures')

import { TransitionalStates, FailureStates, SuccessStates } from '../constants/captures'
import { snakeToPascal } from '../lib/helpers'

export default {
  props: ['capture'],
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
    ...mapActions(['read'])
  }
}
</script>

<style scoped>
.status {
  font-size: 1em;
}
</style>
