<template>
<TheMainHeader
  head="Log in"/>
<form>
  <div class="mb-3">
    <label for="username" class="form-label">Email</label>
    <input v-model="username" id="username" type="text" class="form-control">
  </div>
  <div class="mb-3">
    <label for="password" class="form-label">Password</label>
    <input v-model="password" id="password" type="text" class="form-control">
  </div>
  <button type="submit" class="btn btn-primary">Log in</button>
</form>

  <hr>

<p class="small">
  Don't have an account?
  <router-link :to="{name: 'sign_up'}">Sign up</router-link>
</p>
<p class="small">
  Forgot your password?
  <router-link :to="{name: 'password_reset'}">Reset password</router-link>
</p>
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
