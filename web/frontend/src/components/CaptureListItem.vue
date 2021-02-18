<template>
  <tr>
    <th scope="row">{{ capture.id }}</th>
    <td><a :href=capture.requestedUrl>{{ capture.requestedUrl }}</a></td>
    <td>{{ capture.status }}</td>
    <td>{{ capture.createdAt }}</td>
  </tr>
</template>

<script lang="ts">
export default {
  props: ['capture']
}
</script>

<style scoped>
</style>
