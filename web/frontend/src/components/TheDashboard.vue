<template>
  <div class="capture-dashboard container"
       :class="{'capture-detail': !$store.getters.isMobile && displayedCapture}">
    <CaptureForm/>
    <CaptureList/>
    <capture-detail v-if="!isMobile"/>
  </div>
</template>

<script lang="ts">
import CaptureForm from './CaptureForm.vue'
import CaptureList from './CaptureList.vue'
import CaptureDetail from './CaptureDetail.vue'
import {debounce} from '../lib/helpers';

import { createNamespacedHelpers } from 'vuex'
const {mapState} = createNamespacedHelpers('globals')

export default {
  components: {
    CaptureForm,
    CaptureList,
    CaptureDetail
  },
  computed: {
    isMobile() {
      return this.$store.getters.isMobile;
    },
    displayedCapture() {
      return this.$store.getters.displayedCapture;
    },
    ...mapState({
      rwp_base_url: 'rwp_base_url'
    })
  },

  mounted() {
    this.$store.commit('setWindowWidth');
    this.$store.commit('setViewportHeight');
    this.$nextTick(() => {
      window.addEventListener('resize', debounce(() => {
            this.$store.commit('setWindowWidth');
            this.$store.commit('setViewportHeight');
          }, 250)
      );
    });
    const replay = document.createElement('script')
    replay.setAttribute('src', this.rwp_base_url + '/ui.js')
    document.head.appendChild(replay)
  }
}
</script>

<style lang="scss">
@import "../styles/styles";
@import "../styles/_pages/dashboard";
</style>
