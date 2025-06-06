<template>
  <v-app>
    <v-main>
      <RundownManager/>
    </v-main>
  </v-app>
</template>

<script>
import RundownManager	 from './components/RundownManager.vue'

export default {
  name: 'App',

  components: {
    RundownManager
  },

  data: () => ({
    //
  }),
}
</script>
