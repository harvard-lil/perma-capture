<template>
  <tr>
    <th scope="row">{{ capture.id }}</th>
    <td><a :href=capture.requestedUrl>{{ capture.requestedUrl }}</a></td>
    <td>{{ capture.label }}</td>
    <td><input class="form-check-input" type="checkbox" :value=capture.captureOembedView id="flexCheckDisabled" disabled></td>
    <td><span :class="['badge', 'bg-'+statusBG]">{{ capture.status }}</span></td>
    <td>{{ formattedDate }}</td>
  </tr>
</template>

<script lang="ts">
export default {
  props: ['capture'],
  computed: {
    formattedDate() {
      return (new Date(this.capture.createdAt)).toLocaleDateString()
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
</style>
