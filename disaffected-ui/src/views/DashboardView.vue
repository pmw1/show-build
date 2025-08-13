<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Dashboard</h2>
        <v-row>
          <!-- Quick Stats Cards -->
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Recent Episodes</v-card-title>
              <v-card-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="n in 3"
                    :key="n"
                    :title="`Episode ${n}`"
                    link
                    :to="`/stack/${n}`"
                  ></v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Asset Usage</v-card-title>
              <v-card-text>
                <!-- Placeholder for asset stats -->
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Templates</v-card-title>
              <v-card-text>
                <!-- Placeholder for template stats -->
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'DashboardView'
}
</script>