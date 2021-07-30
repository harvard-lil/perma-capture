<template>
  <div class="container-full two-col login-page-container">
    <WelcomeMessage/>
    <div class="enter-container" v-if="allow_signups">
      <BaseForm :title="'Sign up'"
                :fields="fields"
                submitText="Sign up"
                :action="signUp"/>

      <p class="small">
        Have an account?
        <router-link :to="{name: 'login'}">Log in</router-link>
      </p>
    </div>
    <div class="enter-container" v-else>
      <h2>Interested?</h2>
      <p>Just <a :href="`mailto:${ contact_email }?subject=Request%20A%20Capturing%20Account`">let us know</a> how
        you you'd like to use the service, and we can send you an invitation!</p>
      <p>(While in beta, we are invitation-only, but we plan to be available for general use soon!)</p>
      <p>
        <router-link :to="{name: 'docs'}">Learn more.</router-link>
      </p>
    </div>
  </div>


  <!--      <div class="col">-->
  <!--        <h2>Make an archive</h2>-->
  <!--        <p>Use our state-of-the-art capture service and API to document what you see on the web.</p>-->
  <!--        <h2>Store it where you please</h2>-->
  <!--        <p>Keep it wherever you keep important files. Dropbox? Google Drive? Microsoft One-Drive? Your company's CMS?-->
  <!--          It's totally up to you.</p>-->
  <!--        <h2>Play it back on demand</h2>-->
  <!--        <p>Publish your archives on your website using a <a href="https://replayweb.page/docs/embedding">little-->
  <!--          javascript</a>. Or, review them using the <a-->
  <!--            href="https://github.com/webrecorder/replayweb.page/releases/latest">ReplayWeb.page App</a> or <a-->
  <!--            href="https://replayweb.page/">ReplayWeb.page service</a>.</p>-->
  <!--      </div>-->
</template>

<script lang="ts">
import {createNamespacedHelpers} from 'vuex'

const {mapState} = createNamespacedHelpers('globals')
const {mapActions} = createNamespacedHelpers('user')

import BaseForm from './BaseForm.vue'
import WelcomeMessage from './WelcomeMessage.vue'

export default {
  components: {
    BaseForm,
    WelcomeMessage,
  },
  computed: mapState([
    'app_name',
    'contact_email',
    'allow_signups'
  ]),
  data: () => ({
    fields: [
      {name: 'first_name', label: 'First name'},
      {name: 'last_name', label: 'Last name'},
      {name: 'email', label: 'Email'},
    ]
  }),
  methods: {
    ...mapActions(['signup']),
    signUp(params) {
      return this.signup(params).then(() => window.location = '/')
    }
  }


}
</script>

<style scoped>
</style>
