<template>
  <tr>
    <td><a :href=capture.requested_url>{{ capture.requested_url }}</a></td>
    <td>{{ capture.label }}</td>
    <td><input class="form-check-input" type="checkbox" v-model="capture.capture_oembed_view" id="flexCheckDisabled" disabled></td>
    <td><span :class="['status', 'badge', `bg-${statusBG}`]">{{ statusOrDefault.replace('_', ' ') }}</span></td>
    <td>{{ formattedDate }}</td>
  </tr>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapActions } = createNamespacedHelpers('captures')

const TRANSITIONAL_STATES = ["pending", "in_progress"]

export default {
  poller: null,
  props: ['capture'],
  computed: {
    isProcessing() {
      return this.capture.id && TRANSITIONAL_STATES.includes(this.capture.status)
    },
    statusOrDefault() {
      return this.capture.status || 'pending'
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
    }
  },
  methods: {
    ...mapActions(['read'])
  },
  watch: {
    isProcessing(val, prev) {
      if(val){
        this.$options.poller = setInterval(() => this.read(this.capture), 3000)
      } else {
        clearInterval(this.$options.poller)
      }
    }
  }
}
</script>

<style scoped>
.status:first-letter {
  text-transform: capitalize;
}
</style>
