<template>
  <div class="capture-dashboard container" :class="{'capture-detail': !$store.getters.isMobile && capture}">
    <CaptureForm/>
    <CaptureList/>
    <capture-detail v-if="!$store.getters.isMobile && capture" :capture="capture" />
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
    }
  },
  watch: {
    capture() {
      return this.$store.getters.capture;
    }
  },
  methods: {
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

<style scoped>
</style>
