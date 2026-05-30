<!--
  Development > Wireframes (admin-only).

  An index of interactive region wireframes used to point Claude / the team at a
  specific UI region. Each wireframe is a self-contained static HTML file served
  from /public, opened in a new tab. Add new wireframes to the WIREFRAMES array.
-->
<template>
  <v-container class="py-6" style="max-width: 1000px;">
    <div class="d-flex align-center mb-1">
      <v-icon color="purple-lighten-2" class="mr-2">mdi-vector-rectangle</v-icon>
      <h1 class="text-h5">Wireframes</h1>
    </div>
    <p class="text-body-2 text-grey mb-6">
      Interactive region maps of the app's pages. Open one, then
      <strong>double-click a region</strong> to copy a ready-to-paste focus prompt
      naming that region, its parent, and the route — for pointing at exactly what
      to work on.
    </p>

    <v-row>
      <v-col
        v-for="wf in wireframes"
        :key="wf.file"
        cols="12"
        sm="6"
      >
        <v-card
          class="h-100"
          variant="outlined"
          :href="wf.file"
          target="_blank"
          rel="noopener"
          hover
        >
          <v-card-item>
            <template #prepend>
              <v-icon :icon="wf.icon" color="purple-lighten-2" size="large" />
            </template>
            <v-card-title>{{ wf.title }}</v-card-title>
            <v-card-subtitle>{{ wf.route }}</v-card-subtitle>
          </v-card-item>
          <v-card-text class="text-body-2">{{ wf.description }}</v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              :href="wf.file"
              target="_blank"
              rel="noopener"
              variant="text"
              color="purple-lighten-2"
              append-icon="mdi-open-in-new"
            >Open</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
// Wireframe files live in /public/wireframes/ so they are served as static
// assets (each is a standalone Vue 3 + Vuetify HTML page, no build needed).
const wireframes = [
  {
    title: 'Content Editor',
    route: '/content-editor/:episode?',
    file: '/wireframes/content-editor-wireframe.html',
    icon: 'mdi-script-text-outline',
    description:
      'Region map of the Content Editor: Top App Bar, Show Info Header, and the three columns (Rundown Panel, Editor Panel, Metadata Panel) with all their sub-regions.',
  },
];
</script>
