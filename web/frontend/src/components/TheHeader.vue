<template>
  <header>
    <div class="navbar-brand logo">
      <a href="/">{{ app_name }}</a>
    </div>
    <!-- {% if not request.user.is_authenticated %} -->
    <div class="header-right">
      <a href="#">Sign up</a>
      <a href="#">User Guide</a>
      <a href="#">Log in</a>
    </div>
    <!-- {% endif %} -->
  </header>
</template>

<script lang="ts">
  import { mapState } from 'vuex'

  export default {
      computed: mapState([
          'app_name'
      ])
  }
</script>

<style scoped>
  div {
    color: red;
  }
</style>
