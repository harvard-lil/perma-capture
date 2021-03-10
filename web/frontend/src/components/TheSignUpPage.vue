<template>
<TheNavbar/>
<main>
  <TheMainHeader
    :head="app_name"/>
  <a href="https://perma.cc">Perma.cc</a> is a service that prevents link rot, creating permanent, citable records of web content for authors. <router-link :to="{name: 'root'}">{{ app_name }}</router-link> is powered by the same technology... but delivers the web archive straight to you.
  
  <div class="row mt-5 gx-5">
    <div class="col">
      <h2>Interested?</h2>
      <p>Just <a :href="`mailto:${ contact_email }?subject=Request%20A%20Capturing%20Account`">let us know</a> how you you'd like to use the service, and we can send you an invitation!</p>
      <p>(While in beta, we are invitation-only, but we plan to be available for general use soon!)</p>
      <p><router-link :to="{name: 'docs'}">Learn more.</router-link></p>
    </div>
    
    <div class="col">
      <h2>Make an archive</h2>
      <p>Use our state-of-the-art capture service and API to document what you see on the web.</p>
      <h2>Store it where you please</h2>
      <p>Keep it wherever you keep important files. Dropbox? Google Drive? Microsoft One-Drive? Your company's CMS? It's totally up to you.</p>
      <h2>Play it back on demand</h2>
      <p>Publish your archives on your website using a <a href="https://replayweb.page/docs/embedding">little javascript</a>. Or, review them using the <a href="https://github.com/webrecorder/replayweb.page/releases/latest">ReplayWeb.page App</a> or <a href="https://replayweb.page/">ReplayWeb.page service</a>.</p>
  </div>
</div>
</main>
</template>

<script lang="ts">
import { createNamespacedHelpers } from 'vuex'
const { mapState } = createNamespacedHelpers('globals')

import TheNavbar from './TheNavbar.vue'
import TheMainHeader from './TheMainHeader.vue'

export default {
  components: {
    TheNavbar,
    TheMainHeader
  },
  computed: mapState([
    'app_name',
    'contact_email'
  ])
}
</script>

<style scoped>
</style>
