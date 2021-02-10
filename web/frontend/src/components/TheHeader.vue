<template>
  <header>
    <div class="navbar-brand logo">
      <a href="/">{{ app_name }} <img alt="" class="infinity-logo" src="{% static 'img/eyes.svg' %}"></a>
    </div>
    <!-- {% if not request.user.is_authenticated %} -->
    <div class="header-right">
      <a href="{% url 'sign_up' %}">Sign up</a>
      <a href="{% url 'docs' %}">User Guide</a>
      <a href="{% url 'login' %}">Log in</a>
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
