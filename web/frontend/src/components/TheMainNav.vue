<template>
<div class="dropdown">
  <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton1" data-bs-toggle="dropdown" aria-expanded="false">
    {{ first_name }}
  </button>
  <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdownMenuButton1">
    <template v-if="is_authenticated">
      <li><a class="dropdown-item" href="/user/account/">My Account</a></li>
      <li><a class="dropdown-item" href="/docs/">User Guide</a></li>
      <li><a class="dropdown-item" href="/user/logout/">Log Out</a></li>
    </template>

    <template v-else>
      <li><a class="dropdown-item" href="/sign-up/">Sign up</a></li>
      <li><a class="dropdown-item" href="/docs/">User Guide</a></li>
      <li><a class="dropdown-item" href="/user/login">Log in</a></li>
    </template>
    
    <template v-if="is_staff">
      <li><hr class="dropdown-divider"></li>
      <li><h6 class="dropdown-header">Admin Only</h6></li>
      <li><a class="dropdown-item" href="/admin/">Django Admin</a></li>
      <li><a class="dropdown-item" href="/manage/celery/">Celery Queue Status</a></li>
    </template>
  </ul>
</div>
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
