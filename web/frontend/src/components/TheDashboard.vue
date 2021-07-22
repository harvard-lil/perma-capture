<template>
  <div class="capture-dashboard container" :class="{'capture-detail': !$store.getters.isMobile && capture}">
    <CaptureForm/>
    <CaptureList/>
    <capture-detail v-if="!isMobile && capture" :capture="capture" />
  </div>
</template>

<script lang="ts">
import CaptureForm from './CaptureForm.vue'
import CaptureList from './CaptureList.vue'
import CaptureDetail from './CaptureDetail.vue'
import store from '../store/index.ts';
import {debounce} from '../lib/helpers';

export default {
  components: {
    CaptureForm,
    CaptureList,
    CaptureDetail
  },
  computed: {
    capture() {
      return this.$store.getters.capture;
    },
    isMobile() {
      return this.$store.getters.isMobile;
    }
  },
  watch: {
    capture() {
      return this.$store.getters.capture;
    }
  },

  mounted() {
    this.$store.commit('setWindowWidth')
    this.$nextTick(() => {
      window.addEventListener('resize', debounce(() => {
            this.$store.commit('setWindowWidth')
          }, 250)
      );
    });

  }
}
</script>

<style lang="scss">
@import "../styles/styles";
@import "../styles/_pages/dashboard";
</style>
