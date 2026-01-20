<template>
  <v-container fluid class="money-factory pa-4">
    <v-row>
      <v-col>
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="success">mdi-cash-multiple</v-icon>
            <span>MoneyFactory</span>
          </v-card-title>
        </v-card>

        <v-tabs v-model="activeTab" color="success" class="mt-4 mb-4">
          <v-tab value="customers">
            <v-icon class="mr-2">mdi-domain</v-icon>
            Customers
          </v-tab>
          <v-tab value="invoices" disabled>
            <v-icon class="mr-2">mdi-receipt-text</v-icon>
            Invoices
            <v-chip size="x-small" class="ml-2">Soon</v-chip>
          </v-tab>
          <v-tab value="campaigns" disabled>
            <v-icon class="mr-2">mdi-bullhorn</v-icon>
            Campaigns
            <v-chip size="x-small" class="ml-2">Soon</v-chip>
          </v-tab>
          <v-tab value="reports" disabled>
            <v-icon class="mr-2">mdi-chart-line</v-icon>
            Reports
            <v-chip size="x-small" class="ml-2">Soon</v-chip>
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <v-tabs-window-item value="customers">
            <CustomerManager />
          </v-tabs-window-item>

          <v-tabs-window-item value="invoices">
            <v-card flat class="pa-8 text-center">
              <v-icon size="64" color="grey-lighten-1">mdi-receipt-text-outline</v-icon>
              <h3 class="text-h6 mt-4 text-grey">Invoice Management</h3>
              <p class="text-grey">Coming soon - Track and manage customer invoices</p>
            </v-card>
          </v-tabs-window-item>

          <v-tabs-window-item value="campaigns">
            <v-card flat class="pa-8 text-center">
              <v-icon size="64" color="grey-lighten-1">mdi-bullhorn-outline</v-icon>
              <h3 class="text-h6 mt-4 text-grey">Ad Campaigns</h3>
              <p class="text-grey">Coming soon - Manage advertising campaigns and placements</p>
            </v-card>
          </v-tabs-window-item>

          <v-tabs-window-item value="reports">
            <v-card flat class="pa-8 text-center">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-line</v-icon>
              <h3 class="text-h6 mt-4 text-grey">Revenue Reports</h3>
              <p class="text-grey">Coming soon - Analytics and revenue tracking</p>
            </v-card>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import CustomerManager from '@/components/settings/CustomerManager.vue'

export default {
  name: 'MoneyFactoryView',
  components: {
    CustomerManager
  },
  data() {
    return {
      activeTab: 'customers'
    }
  }
}
</script>

<style scoped>
.money-factory {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
