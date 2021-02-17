<template>
  <form>    
    <div class="field">
      <label for="urls" class="label">URLs</label>
      <div class="control">
        <textarea id="urls" rows="3" required="" placeholder="Enter one or more URLs on each line" aria-describedby="urls-errors" class="textarea " aria-invalid="false"></textarea>
      </div>
    </div>

    <div class="field">
      <label class="checkbox">
        <input id="embed" type="checkbox" class="checkbox">
        Archive Embedded Version (if available)
      </label>
    </div>

    <div class="field">
      <label for="tag" class="label">Label (Optional)</label>
      <div class="control">
        <input id="tag" type="text" class="input" value="">
      </div>
    </div>

    <div class="submit-error">
      <div class="field">
        <div class="control">
          <button type="submit" class="button is-link">Capture</button>
        </div>
      </div>
    </div>
  </form>
</template>

<script lang="ts">
</script>

<style scoped>
</style>
