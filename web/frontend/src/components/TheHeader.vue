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
header {
  background-color: white;
  padding: 20px 0;
  width: 100%;
  text-align: left;
  display: flex;
  justify-content: space-between;
  font-size: 24px;
}

.header-right {
  padding-right: 36px;
  padding-left: 36px;
  font-size: 18px;
  margin-top: 6px;
  font-weight: 300;
}

.header-right a {
  padding-left: 12px;
}

.logo a {
  font-weight: 900;
  color: #222;
  padding-left: 36px;
  min-width: 7em;
}
</style>
