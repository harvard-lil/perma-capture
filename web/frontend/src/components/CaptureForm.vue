<template>
<form class="capture-form p-3">
  <div class="mb-3">
    <label for="urls" class="form-label">URLs</label>
    <textarea id="urls" class="form-control" rows="3" required="" placeholder="Enter one or more URLs on each line" aria-describedby="urls-errors" aria-invalid="false"></textarea>
  </div>
  
  <div class="mb-3 form-check">
    <input id="embed" type="checkbox" class="form-check-input">
    <label for="embed" class="form-check-label">Archive Embedded Version (if available)</label>
  </div>
  
  <div class="mb-3">
    <label for="tag" class="form-label">Label (Optional)</label>
    <input id="tag" type="text" class="form-control" value="">
  </div>
  
  <button type="submit" class="btn btn-primary mb-3">Capture</button>
</form>
</template>

<script lang="ts">
</script>

<style scoped>
  .capture-form {
    background: var(--color-background);
  }
</style>
