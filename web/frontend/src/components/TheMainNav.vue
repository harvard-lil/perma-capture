<template>
  <div v-if="is_authenticated" class="dropdown">
    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdown-menu-nav" data-bs-toggle="dropdown"
            aria-expanded="false">
      {{ first_name }}
    </button>
    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdown-menu-nav">
      <li>
        <router-link :to="{name: 'root'}" class="dropdown-item">Dashboard</router-link>
      </li>
      <li>
        <router-link :to="{name: 'account'}" class="dropdown-item">My Account</router-link>
      </li>
      <li>
        <router-link :to="{name: 'docs'}" class="dropdown-item">User Guide</router-link>
      </li>
      <li><a class="dropdown-item">Log Out</a></li>

      <template v-if="is_staff">
        <li>
          <hr class="dropdown-divider">
        </li>
        <li><h6 class="dropdown-header">Admin Only</h6></li>
        <li><a class="dropdown-item" href="/admin/">Django Admin</a></li>
      </template>
    </ul>
  </div>

  <ul v-else class="navbar-nav">
    <li class="nav-item">
      <router-link :to="{name: 'sign_up'}" class="nav-link">Sign up</router-link>
    </li>
    <li class="nav-item">
      <router-link :to="{name: 'docs'}" class="nav-link">User Guide</router-link>
    </li>
    <li class="nav-item">
      <router-link :to="{name: 'login'}" class="nav-link">Log in</router-link>
    </li>
  </ul>
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapState} = createNamespacedHelpers('user')

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
