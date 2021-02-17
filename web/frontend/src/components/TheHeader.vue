<template>
  <header id="header">
    <a href="/" class="brand">
      {{ app_name }} <img alt="" class="logo" src="/static/img/eyes.svg">
    </a>
    <div class="header-right">
      <a href="#">Sign up</a>
      <a href="#">User Guide</a>
      <a href="#">Log in</a>
    </div>
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
#header {
  background-color: white;
  padding: 20px 0;
  width: 100%;
  text-align: left;
  display: flex;
  justify-content: space-between;
  font-size: 24px;
}

#header a:hover,
#header a:focus {
  color: #DD671A;
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

.brand {
  font-weight: 900;
  color: #222;
  padding-left: 36px;
  min-width: 7em;
}

.logo {
  height: 15px;
  margin-left: 5px;
}
</style>
