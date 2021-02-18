<template>
  <tr>
    <th scope="row">{{ capture.id }}</th>
    <td><a :href=capture.requestedUrl>{{ capture.requestedUrl }}</a></td>
    <td>{{ capture.status }}</td>
    <td>{{ formattedDate }}</td>
  </tr>
</template>

<script lang="ts">
export default {
  props: ['capture'],
  computed: {
    formattedDate() {
      return (new Date(this.capture.createdAt)).toLocaleDateString()
    }
  }
}
</script>

<style scoped>
</style>
