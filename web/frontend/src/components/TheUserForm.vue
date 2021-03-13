<template>
<form>
  <div class="mb-3">
    <label for="first_name" class="form-label">First name</label>
    <input v-model="first_name" id="first_name" type="text" class="form-control">
  </div>
  <div class="mb-3">
    <label for="last_name" class="form-label">Last name</label>
    <input v-model="last_name" id="first_name" type="text" class="form-control">
  </div>
  <div class="mb-3">
    <label for="email" class="form-label">Email</label>
    <input v-model="email" id="first_name" type="text" class="form-control">
  </div>
  <button type="submit" class="btn btn-primary">Save changes</button>
</form>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState, mapActions } = createNamespacedHelpers('user')

export default {
  computed: mapState([
    'first_name',
    'last_name',
    'email'
  ]),
  methods: {
    ...mapActions(['resetToken'])
  }
}
</script>

<style>
</style>
