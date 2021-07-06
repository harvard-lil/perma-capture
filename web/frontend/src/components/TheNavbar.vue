<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container-fluid">
      <router-link :to="{name: 'root'}" class="navbar-brand">
        <img alt="Perma logo" title="Perma logo" src="../assets/img/perma-logo.svg">
        Perma Capture
      </router-link>
      <TheMainNav/>
    </div>
  </nav>
</template>


<script>
import TheMainNav from './TheMainNav.vue';
import {createNamespacedHelpers} from 'vuex';

const {mapState} = createNamespacedHelpers('globals');

export default {
  components: {
    TheMainNav,
  },
}
</script>
