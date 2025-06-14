<template>
  <v-app>
    <!-- Top App Bar -->
    <v-app-bar 
      color="surface"
      elevation="1"
    >
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
      ></v-app-bar-nav-icon>

      <v-app-bar-title class="text-primary font-weight-bold">
        Show Builder
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- User Menu -->
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon
            v-bind="props"
          >
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            v-for="(item, i) in userMenuItems"
            :key="i"
            :prepend-icon="item.icon"
            :title="item.title"
            @click="handleUserMenuItem(item)"
          >
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      temporary
    >
      <v-list density="compact" nav>
        <v-list-item
          v-for="(item, i) in navItems"
          :key="i"
          :value="item"
          :to="item.to"
          :prepend-icon="item.icon"
        >
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content Area -->
    <v-main>
      <v-container fluid class="pa-0">
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App',
  data: () => ({
    drawer: false,
    navItems: [
      {
        title: 'Dashboard',
        icon: 'mdi-view-dashboard',
        to: '/dashboard'
      },
      {
        title: 'Rundown Editor',
        icon: 'mdi-playlist-edit',
        to: '/rundown'
      },
      {
        title: 'Asset Manager',
        icon: 'mdi-folder',
        to: '/assets'
      },
      {
        title: 'Templates',
        icon: 'mdi-file-document',
        to: '/templates'
      },
      {
        title: 'Settings',
        icon: 'mdi-cog',
        to: '/settings'
      }
    ],
    userMenuItems: [
      {
        title: 'Profile',
        icon: 'mdi-account',
        action: 'profile'
      },
      {
        title: 'Settings',
        icon: 'mdi-cog',
        action: 'settings'
      },
      {
        title: 'Logout',
        icon: 'mdi-logout',
        action: 'logout'
      }
    ]
  }),
  methods: {
    handleUserMenuItem(item) {
      console.log(`User menu action: ${item.action}`);
      // Implement user menu actions
    }
  }
}
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.v-main {
  background: #f5f5f5;
  padding-top: 64px !important;  /* Add padding equal to app bar height */
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-bottom: 0 !important;
}

.v-main .v-container {
  max-width: none;
  padding: 0 !important;
}
</style>
