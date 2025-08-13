<template>
  <v-container fluid class="pa-4">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col>
        <h2 class="text-h4 font-weight-bold">Episodes</h2>
      </v-col>
      <v-col class="text-right">
        <v-btn
          color="primary"
          @click="createNewEpisode"
          prepend-icon="mdi-plus"
        >
          New Episode
        </v-btn>
      </v-col>
    </v-row>

    <!-- Filter and Search Bar -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search episodes..."
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Status"
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="dateFilter"
          :items="dateFilterOptions"
          label="Date Range"
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" md="2" class="text-right">
        <v-btn
          icon="mdi-refresh"
          @click="fetchEpisodes"
          :loading="loading"
        />
      </v-col>
    </v-row>

    <!-- Episodes Table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="filteredEpisodes"
        :search="search"
        :loading="loading"
        :sort-by="[{ key: 'episode_number', order: 'desc' }]"
        class="elevation-1"
        hover
      >
        <!-- Episode Number Column -->
        <template v-slot:[`item.episode_number`]="{ item }">
          <v-chip
            color="primary"
            variant="tonal"
            size="small"
          >
            {{ item.episode_number }}
          </v-chip>
        </template>

        <!-- Title Column -->
        <template v-slot:[`item.title`]="{ item }">
          <div>
            <div class="font-weight-medium">{{ item.title || `Episode ${item.episode_number}` }}</div>
            <div v-if="item.subtitle" class="text-caption text-grey">{{ item.subtitle }}</div>
          </div>
        </template>

        <!-- Air Date Column -->
        <template v-slot:[`item.airdate`]="{ item }">
          <div v-if="item.airdate">
            {{ formatDate(item.airdate) }}
            <v-chip
              v-if="isUpcoming(item.airdate)"
              color="info"
              size="x-small"
              class="ml-2"
            >
              Upcoming
            </v-chip>
          </div>
          <span v-else class="text-grey">Not scheduled</span>
        </template>

        <!-- Status Column -->
        <template v-slot:[`item.status`]="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            variant="flat"
            size="small"
          >
            {{ item.status || 'Unknown' }}
          </v-chip>
        </template>

        <!-- Duration Column -->
        <template v-slot:[`item.duration`]="{ item }">
          <span v-if="item.duration">{{ item.duration }}</span>
          <span v-else class="text-grey">--:--:--</span>
        </template>

        <!-- Guest Column -->
        <template v-slot:[`item.guest`]="{ item }">
          <span v-if="item.guest">{{ item.guest }}</span>
          <span v-else class="text-grey">No guests</span>
        </template>

        <!-- Actions Column -->
        <template v-slot:[`item.actions`]="{ item }">
          <v-btn
            icon="mdi-pencil"
            size="small"
            variant="text"
            @click="editEpisode(item)"
            title="Edit episode"
          />
          <v-btn
            icon="mdi-playlist-edit"
            size="small"
            variant="text"
            @click="openRundown(item)"
            title="Edit rundown"
          />
          <v-btn
            icon="mdi-content-copy"
            size="small"
            variant="text"
            @click="duplicateEpisode(item)"
            title="Duplicate episode"
          />
          <v-btn
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
            @click="deleteEpisode(item)"
            title="Delete episode"
          />
        </template>

        <!-- Loading slot -->
        <template v-slot:loading>
          <v-skeleton-loader type="table-row-divider@10" />
        </template>

        <!-- No data slot -->
        <template v-slot:no-data>
          <v-empty-state
            headline="No episodes found"
            text="Create your first episode to get started"
            icon="mdi-television-classic-off"
          >
            <template v-slot:actions>
              <v-btn
                color="primary"
                @click="createNewEpisode"
              >
                Create First Episode
              </v-btn>
            </template>
          </v-empty-state>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create/Edit Episode Dialog -->
    <v-dialog
      v-model="episodeDialog"
      max-width="600"
      persistent
    >
      <v-card>
        <v-card-title>
          {{ editingEpisode ? 'Edit Episode' : 'Create New Episode' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="episodeForm">
            <v-text-field
              v-model="episodeForm.episode_number"
              label="Episode Number"
              :rules="[v => !!v || 'Episode number is required', v => /^\d{4}$/.test(v) || 'Must be 4 digits']"
              variant="outlined"
              density="comfortable"
              :disabled="editingEpisode"
            />
            <v-text-field
              v-model="episodeForm.show_id"
              label="Show Asset ID"
              type="number"
              :rules="[v => !!v || 'Show ID is required']"
              hint="Links to parent show"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.rundown_id"
              label="Rundown Asset ID"
              type="number"
              :rules="[v => !!v || 'Rundown ID is required']"
              hint="Every episode must have a rundown"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.title"
              label="Title"
              :rules="[v => !!v || 'Title is required']"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.subtitle"
              label="Subtitle (optional)"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.airdate"
              label="Air Date"
              type="date"
              variant="outlined"
              density="comfortable"
            />
            <v-select
              v-model="episodeForm.status"
              :items="['draft', 'scheduled', 'recording', 'post-production', 'published', 'archived']"
              label="Status"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.duration"
              label="Duration (HH:MM:SS)"
              placeholder="01:00:00"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="episodeForm.guest"
              label="Guest(s)"
              variant="outlined"
              density="comfortable"
            />
            <v-textarea
              v-model="episodeForm.description"
              label="Description"
              variant="outlined"
              density="comfortable"
              rows="3"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeEpisodeDialog"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="saveEpisode"
            :loading="saving"
          >
            {{ editingEpisode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog
      v-model="deleteDialog"
      max-width="400"
    >
      <v-card>
        <v-card-title>Delete Episode?</v-card-title>
        <v-card-text>
          Are you sure you want to delete episode {{ episodeToDelete?.episode_number }}:
          "{{ episodeToDelete?.title }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="deleteDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="confirmDelete"
            :loading="deleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import axios from 'axios';
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'EpisodesView',
  setup() {
    const router = useRouter();
    
    // Data
    const episodes = ref([]);
    const loading = ref(false);
    const saving = ref(false);
    const deleting = ref(false);
    const search = ref('');
    const statusFilter = ref(null);
    const dateFilter = ref(null);
    const episodeDialog = ref(false);
    const deleteDialog = ref(false);
    const editingEpisode = ref(false);
    const episodeToDelete = ref(null);
    const episodeForm = ref({
      episode_number: '',
      show_id: 100,  // Default show ID - should come from show configuration
      rundown_id: 0,  // Will be generated
      title: '',
      subtitle: '',
      airdate: '',
      status: 'draft',
      duration: '01:00:00',
      guest: '',
      description: ''
    });

    // Table headers
    const headers = [
      { title: 'Episode', key: 'episode_number', width: '100px' },
      { title: 'Title', key: 'title' },
      { title: 'Air Date', key: 'airdate', width: '150px' },
      { title: 'Status', key: 'status', width: '130px' },
      { title: 'Duration', key: 'duration', width: '100px' },
      { title: 'Guest', key: 'guest', width: '150px' },
      { title: 'Actions', key: 'actions', sortable: false, width: '180px' }
    ];

    // Options
    const statusOptions = [
      'draft',
      'scheduled',
      'recording',
      'post-production',
      'published',
      'archived'
    ];

    const dateFilterOptions = [
      { title: 'All Time', value: 'all' },
      { title: 'This Week', value: 'week' },
      { title: 'This Month', value: 'month' },
      { title: 'Last 3 Months', value: '3months' },
      { title: 'This Year', value: 'year' }
    ];

    // Computed
    const filteredEpisodes = computed(() => {
      let result = [...episodes.value];
      
      // Filter by status
      if (statusFilter.value) {
        result = result.filter(ep => ep.status === statusFilter.value);
      }
      
      // Filter by date range
      if (dateFilter.value && dateFilter.value !== 'all') {
        const now = new Date();
        const filterDate = new Date();
        
        switch (dateFilter.value) {
          case 'week':
            filterDate.setDate(now.getDate() - 7);
            break;
          case 'month':
            filterDate.setMonth(now.getMonth() - 1);
            break;
          case '3months':
            filterDate.setMonth(now.getMonth() - 3);
            break;
          case 'year':
            filterDate.setFullYear(now.getFullYear() - 1);
            break;
        }
        
        result = result.filter(ep => {
          if (!ep.airdate) return false;
          const epDate = new Date(ep.airdate);
          return epDate >= filterDate;
        });
      }
      
      return result;
    });

    // Methods
    const fetchEpisodes = async () => {
      loading.value = true;
      try {
        const response = await axios.get('/api/episodes');
        episodes.value = response.data.episodes || [];
        
        // Fetch additional info for each episode
        for (const episode of episodes.value) {
          try {
            const infoResponse = await axios.get(`/api/episodes/${episode.episode_number}/info`);
            Object.assign(episode, infoResponse.data.info);
          } catch (error) {
            console.warn(`Could not fetch info for episode ${episode.episode_number}`);
          }
        }
      } catch (error) {
        console.error('Failed to fetch episodes:', error);
      } finally {
        loading.value = false;
      }
    };

    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    };

    const isUpcoming = (dateString) => {
      if (!dateString) return false;
      const date = new Date(dateString);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return date >= today;
    };

    const getStatusColor = (status) => {
      const colors = {
        'draft': 'grey',
        'scheduled': 'blue',
        'recording': 'orange',
        'post-production': 'purple',
        'published': 'green',
        'archived': 'brown'
      };
      return colors[status] || 'grey';
    };

    const createNewEpisode = () => {
      editingEpisode.value = false;
      // Generate a unique rundown ID based on episode number
      const episodeNum = getNextEpisodeNumber();
      const rundownId = parseInt(episodeNum + '000'); // e.g., 0237000
      
      episodeForm.value = {
        episode_number: episodeNum,
        show_id: 100,  // TODO: Get from show configuration
        rundown_id: rundownId,
        title: '',
        subtitle: '',
        airdate: getNextSaturday(),
        status: 'draft',
        duration: '01:00:00',
        guest: '',
        description: ''
      };
      episodeDialog.value = true;
    };

    const getNextEpisodeNumber = () => {
      if (episodes.value.length === 0) return '0001';
      const numbers = episodes.value.map(ep => parseInt(ep.episode_number)).filter(n => !isNaN(n));
      const maxNumber = Math.max(...numbers);
      return String(maxNumber + 1).padStart(4, '0');
    };

    const getNextSaturday = () => {
      const today = new Date();
      const dayOfWeek = today.getDay();
      const daysUntilSaturday = (6 - dayOfWeek + 7) % 7 || 7;
      const nextSaturday = new Date(today);
      nextSaturday.setDate(today.getDate() + daysUntilSaturday);
      return nextSaturday.toISOString().split('T')[0];
    };

    const editEpisode = async (episode) => {
      editingEpisode.value = true;
      
      // Fetch full episode info
      try {
        const response = await axios.get(`/api/episodes/${episode.episode_number}/info`);
        episodeForm.value = {
          episode_number: episode.episode_number,
          show_id: response.data.info.show_id || 100,  // Default to 100 if not set
          rundown_id: response.data.info.rundown_id || parseInt(episode.episode_number + '000'),
          title: response.data.info.title || '',
          subtitle: response.data.info.subtitle || '',
          airdate: response.data.info.airdate || '',
          status: response.data.info.status || 'draft',
          duration: response.data.info.duration || '01:00:00',
          guest: response.data.info.guest || '',
          description: response.data.body || ''
        };
        episodeDialog.value = true;
      } catch (error) {
        console.error('Failed to fetch episode info:', error);
      }
    };

    const openRundown = (episode) => {
      router.push(`/content-editor/${episode.episode_number}`);
    };

    const duplicateEpisode = async (episode) => {
      const newNumber = getNextEpisodeNumber();
      editingEpisode.value = false;
      const rundownId = parseInt(newNumber + '000'); // Generate new rundown ID
      episodeForm.value = {
        ...episode,
        episode_number: newNumber,
        show_id: episode.show_id || 100,
        rundown_id: rundownId,
        title: `${episode.title} (Copy)`,
        airdate: getNextSaturday(),
        status: 'draft'
      };
      episodeDialog.value = true;
    };

    const deleteEpisode = (episode) => {
      episodeToDelete.value = episode;
      deleteDialog.value = true;
    };

    const confirmDelete = async () => {
      if (!episodeToDelete.value) return;
      
      deleting.value = true;
      try {
        // TODO: Implement delete endpoint
        console.log('Delete episode:', episodeToDelete.value.episode_number);
        // await axios.delete(`/api/episodes/${episodeToDelete.value.episode_number}`);
        
        // Remove from local list
        const index = episodes.value.findIndex(ep => ep.episode_number === episodeToDelete.value.episode_number);
        if (index > -1) {
          episodes.value.splice(index, 1);
        }
        
        deleteDialog.value = false;
      } catch (error) {
        console.error('Failed to delete episode:', error);
      } finally {
        deleting.value = false;
        episodeToDelete.value = null;
      }
    };

    const closeEpisodeDialog = () => {
      episodeDialog.value = false;
      episodeForm.value = {
        episode_number: '',
        show_id: 100,
        rundown_id: 0,
        title: '',
        subtitle: '',
        airdate: '',
        status: 'draft',
        duration: '01:00:00',
        guest: '',
        description: ''
      };
    };

    const saveEpisode = async () => {
      saving.value = true;
      try {
        const data = {
          ...episodeForm.value,
          type: 'full_show',
          slug: `episode-${episodeForm.value.episode_number}`
        };
        
        if (editingEpisode.value) {
          // Update existing episode
          await axios.put(`/api/episodes/${data.episode_number}/info`, data);
        } else {
          // Create new episode
          await axios.post(`/api/episodes/${data.episode_number}/create`, data);
        }
        
        await fetchEpisodes();
        closeEpisodeDialog();
      } catch (error) {
        console.error('Failed to save episode:', error);
      } finally {
        saving.value = false;
      }
    };

    // Lifecycle
    onMounted(() => {
      fetchEpisodes();
    });

    return {
      episodes,
      loading,
      saving,
      deleting,
      search,
      statusFilter,
      dateFilter,
      episodeDialog,
      deleteDialog,
      editingEpisode,
      episodeToDelete,
      episodeForm,
      headers,
      statusOptions,
      dateFilterOptions,
      filteredEpisodes,
      fetchEpisodes,
      formatDate,
      isUpcoming,
      getStatusColor,
      createNewEpisode,
      editEpisode,
      openRundown,
      duplicateEpisode,
      deleteEpisode,
      confirmDelete,
      closeEpisodeDialog,
      saveEpisode
    };
  }
};
</script>

<style scoped>
.v-data-table {
  font-size: 0.875rem;
}

.v-chip {
  font-weight: 500;
}
</style>