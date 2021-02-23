<template>
<div v-if="is_authenticated" class="dropdown">
  <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton1" data-bs-toggle="dropdown" aria-expanded="false">
    {{ first_name }}
  </button>
  <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdownMenuButton1">
    <li><a class="dropdown-item" href="/user/account/">My Account</a></li>
    <li><a class="dropdown-item" href="/docs/">User Guide</a></li>
    <li><a class="dropdown-item" href="/user/logout/">Log Out</a></li>
    
    <template v-if="is_staff">
      <li><hr class="dropdown-divider"></li>
      <li><h6 class="dropdown-header">Admin Only</h6></li>
      <li><a class="dropdown-item" href="/admin/">Django Admin</a></li>
      <li><a class="dropdown-item" href="/manage/celery/">Celery Queue Status</a></li>
    </template>
  </ul>
</div>

<ul v-else class="navbar-nav">
  <li class="nav-item"><a class="nav-link" href="/sign-up/">Sign up</a></li>
  <li class="nav-item"><a class="nav-link" href="/docs/">User Guide</a></li>
  <li class="nav-item"><a class="nav-link" href="/user/login">Log in</a></li>
</ul>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('user')

export default {
  computed: mapState([
    'first_name',
    'is_authenticated',
    'is_staff'
  ])
}
</script>

<style scoped>
</style>
