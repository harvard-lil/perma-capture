<template>
<TheMainHeader
  head="Forgot your password?"
  subhead="We'll email you instructions for setting a new one."/>
<form>
  <div class="mb-3">
    <label for="username" class="form-label">Email</label>
    <input v-model="username" id="username" type="text" class="form-control">
  </div>
  <button type="submit" class="btn btn-primary">Reset my password</button>
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
