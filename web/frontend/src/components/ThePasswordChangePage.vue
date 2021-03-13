<template>
<TheMainHeader
  head="Change password"/>
<form>
  <div class="mb-3">
    <label for="old_password" class="form-label">Old password</label>
    <input v-model="old_password" id="old_password" type="text" class="form-control">
  </div>
  <div class="mb-3">
    <label for="new_password1" class="form-label">New password</label>
    <input v-model="new_password1" id="new_password1" type="text" class="form-control">
  </div>
  <div class="mb-3">
    <label for="new_password2" class="form-label">New password confirmation</label>
    <input v-model="new_password2" id="new_password2" type="text" class="form-control">
  </div>
  <button type="submit" class="btn btn-primary">Change my password</button>
</form>
</template>

<script lang="ts">
import TheMainHeader from './TheMainHeader.vue'

export default {
  components: {
    TheMainHeader
  }
}
</script>

<style>
</style>
