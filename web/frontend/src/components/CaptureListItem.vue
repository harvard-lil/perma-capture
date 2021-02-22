<template>
  <tr>
    <th scope="row">{{ capture.id }}</th>
    <td><a :href=capture.requested_url>{{ capture.requested_url }}</a></td>
    <td>{{ capture.label }}</td>
    <td><input class="form-check-input" type="checkbox" :value=capture.capture_oembed_view id="flexCheckDisabled" disabled></td>
    <td><span :class="['status', 'badge', 'bg-'+statusBG]">{{ capture.status.replace('_', ' ') }}</span></td>
    <td>{{ formattedDate }}</td>
  </tr>
</template>

<script lang="ts">
export default {
  props: ['capture'],
  computed: {
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
      }[this.capture.status]
    }
  }
}
</script>

<style scoped>
.status:first-letter {
  text-transform: capitalize;
}
</style>
