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
            rounded="0"
            class="full-cell-chip episode-number-chip"
          >
            {{ formatEpisodeNumber(item.episode_number) }}
          </v-chip>
        </template>

        <!-- Title Column -->
        <template v-slot:[`item.title`]="{ item }">
          <div>
            <div class="font-weight-medium">{{ item.title || `Episode ${formatEpisodeNumber(item.episode_number)}` }}</div>
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
            rounded="0"
            class="full-cell-chip"
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
          
          <!-- Production Tools -->
          <v-divider vertical class="mx-1" />
          <v-btn
            icon="mdi-calculator"
            size="small"
            variant="text"
            @click="calculateDuration(item)"
            title="Calculate Duration"
            :loading="item.calculatingDuration"
          />
          <v-btn
            icon="mdi-script-text"
            size="small"
            variant="text"
            @click="generateScript(item)"
            title="Generate Script"
            :loading="item.generatingScript"
          />
          <v-btn
            icon="mdi-folder-multiple"
            size="small"
            variant="text"
            @click="collectMedia(item)"
            title="Collect Media for vMix"
            :loading="item.collectingMedia"
          />
          
          <!-- Other Actions -->
          <v-divider vertical class="mx-1" />
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
        <v-card-text class="pa-6">
          <v-form ref="episodeViewFormRef" class="episode-form">
            <!-- Template Selection -->
            <v-select
              v-model="episodeForm.template_id"
              :items="availableTemplates"
              item-title="name"
              item-value="id"
              label="Episode Template"
              variant="outlined"
              density="comfortable"
              persistent-hint
              hint="Select blueprint template for episode structure"
              class="mb-4"
              :loading="loadingTemplates"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item
                  v-bind="props"
                >
                  <template v-slot:title>
                    {{ item.raw.name }}
                    <v-chip
                      v-if="item.raw.is_default"
                      size="x-small"
                      color="primary"
                      class="ml-2"
                    >
                      Default
                    </v-chip>
                  </template>
                  <template v-slot:subtitle>
                    {{ item.raw.description }}
                  </template>
                </v-list-item>
              </template>
            </v-select>

            <!-- Episode Number and Air Date (with confirmation) -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="episodeForm.episode_number"
                  label="Episode Number"
                  variant="outlined"
                  density="comfortable"
                  persistent-hint
                  hint="Auto-generated, confirm or modify"
                  class="mb-3"
                  :loading="loadingNextNumber"
                >
                  <template v-slot:append-inner>
                    <v-btn
                      icon="mdi-refresh"
                      size="small"
                      variant="text"
                      @click="loadNextEpisodeNumber"
                      :loading="loadingNextNumber"
                      title="Get next available number"
                    />
                  </template>
                </v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="episodeForm.airdate"
                  label="Air Date"
                  type="date"
                  variant="outlined"
                  density="comfortable"
                  persistent-hint
                  hint="Auto-calculated next Sunday, confirm or modify"
                  class="mb-3"
                />
              </v-col>
            </v-row>

            <!-- Episode Details -->
            <v-text-field
              v-model="episodeForm.title"
              :label="editingEpisode ? 'Episode Title' : 'Episode Title (Optional)'"
              :hint="editingEpisode ? '' : 'Can be set later during content development'"
              variant="outlined"
              density="comfortable"
              :persistent-hint="!editingEpisode"
              class="mb-3"
            />

            <!-- Additional fields for editing -->
            <div v-if="editingEpisode">
              <v-text-field
                v-model="episodeForm.subtitle"
                label="Episode Subtitle"
                variant="outlined"
                density="comfortable"
                class="mb-3"
              />
              
              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="episodeForm.status"
                    :items="statusOptions"
                    label="Status"
                    variant="outlined"
                    density="comfortable"
                    class="mb-3"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="episodeForm.duration"
                    label="Duration"
                    placeholder="01:00:00"
                    variant="outlined"
                    density="comfortable"
                    class="mb-3"
                  />
                </v-col>
              </v-row>
              
              <v-text-field
                v-model="episodeForm.guest"
                label="Guest(s)"
                variant="outlined"
                density="comfortable"
                class="mb-3"
              />
              
              <v-textarea
                v-model="episodeForm.description"
                label="Episode Description"
                variant="outlined"
                density="comfortable"
                rows="3"
                class="mb-3"
              />
            </div>

            <!-- Creation Info (show only for new episodes) -->
            <v-alert
              v-if="!editingEpisode"
              type="info"
              variant="tonal"
              class="mb-0"
            >
              <strong>Episode will be created with:</strong><br>
              • Status: Draft<br>
              • AssetID: Auto-generated via API<br>
              • Complete directory structure with info.md<br>
              • Database record for tracking
            </v-alert>
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
      max-width="500"
    >
      <v-card>
        <v-card-title class="text-error">
          <v-icon class="mr-2" color="error">mdi-alert-circle</v-icon>
          Delete Episode {{ episodeToDelete?.episode_number }}?
        </v-card-title>
        <v-card-text class="pb-2">
          <div class="mb-3">
            <strong>Episode:</strong> {{ episodeToDelete?.episode_number }}: "{{ episodeToDelete?.title || 'Untitled' }}"
          </div>
          
          <v-alert
            type="warning"
            variant="tonal"
            class="mb-3"
          >
            <strong>⚠️ This will permanently remove:</strong>
            <ul class="mt-2 mb-0">
              <li>All episode files from the filesystem</li>
              <li>Complete episode directory structure</li>
              <li>Episode record from the database</li>
              <li>All rundown items and content</li>
              <li>Associated media and assets</li>
            </ul>
          </v-alert>
          
          <div class="text-error font-weight-bold">
            This action cannot be undone!
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
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
            prepend-icon="mdi-delete-forever"
          >
            Delete Permanently
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
import { getColorValue, loadColorsFromDatabase } from '@/utils/themeColorMap.js';

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
      template_id: null,
      title: '',
      airdate: ''
    });

    // New template-related data
    const availableTemplates = ref([]);
    const loadingTemplates = ref(false);
    const loadingNextNumber = ref(false);

    // Table headers
    const headers = [
      { title: 'Ep', key: 'episode_number', width: '60px' },
      { title: 'Status', key: 'status', width: '80px' },
      { title: 'Title', key: 'title', width: '200px' },
      { title: 'Air Date', key: 'airdate', width: '150px' },
      { title: 'Duration', key: 'duration', width: '100px' },
      { title: 'Guest', key: 'guest', width: '150px' },
      { title: 'Actions', key: 'actions', sortable: false, width: '280px' }
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

    // eslint-disable-next-line no-unused-vars
    const templateOptions = [
      { title: 'Sunday Show', value: 'sunday_show' },
      { title: 'Full Show', value: 'full_show' },
      { title: 'Interview', value: 'interview' },
      { title: 'Custom', value: 'custom' }
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
      // Use the Show-Build color system for status colors
      if (!status) return getColorValue('unknown');
      
      const statusLower = status.toLowerCase();
      
      // Map episode statuses to Show-Build color system
      const statusColorMap = {
        'draft': getColorValue('draft'),           // grey-darken-2
        'approved': getColorValue('approved'),     // green-accent
        'production': getColorValue('production'), // blue-accent  
        'completed': getColorValue('completed'),   // yellow-accent
        // Legacy mappings for backwards compatibility
        'scheduled': getColorValue('approved'),
        'recording': getColorValue('production'),
        'post-production': getColorValue('production'),
        'published': getColorValue('completed'),
        'archived': getColorValue('completed'),
        'unknown': getColorValue('unknown')
      };
      
      return statusColorMap[statusLower] || getColorValue('unknown');
    };

    const formatEpisodeNumber = (episodeNumber) => {
      if (!episodeNumber) return '0000';
      return episodeNumber.toString().padStart(4, '0');
    };

    const createNewEpisode = async () => {
      editingEpisode.value = false;
      
      // Load templates and next episode number in parallel
      try {
        await Promise.all([
          loadTemplates(),
          loadNextEpisodeNumber()
        ]);
        
        // Give Vue time to process reactivity updates before opening dialog
        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        console.error('Error loading episode creation data:', error);
      }
      
      episodeDialog.value = true;
    };

    const loadTemplates = async () => {
      loadingTemplates.value = true;
      try {
        // Try loading from API with proper authentication
        const response = await axios.get('/api/episodes/templates', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        
        console.log('Templates API response:', response.data);
        availableTemplates.value = response.data || [];
        
        // Set default template selection
        if (availableTemplates.value && availableTemplates.value.length > 0) {
          const defaultTemplate = availableTemplates.value.find(t => 
            t.is_default === true
          ) || availableTemplates.value[0];
          
          if (defaultTemplate) {
            episodeForm.value.template_id = defaultTemplate.id;
            console.log('Default template selected:', defaultTemplate);
          }
        } else {
          console.warn('No templates returned from API, using fallback');
          throw new Error('Empty templates response');
        }
        
      } catch (error) {
        console.error('Failed to load templates from API:', error);
        console.error('Error response:', error.response?.data);
        
        // Create fallback templates that match the API structure
        availableTemplates.value = [
          {
            id: 1,
            name: 'Sunday Show (Default)',
            description: 'Standard Sunday show template',
            template_type: 'episode',
            is_default: true,
            is_active: true
          },
          {
            id: 2,
            name: 'Full Show',
            description: 'Complete show template',
            template_type: 'episode',
            is_default: false,
            is_active: true
          },
          {
            id: 3,
            name: 'Interview',
            description: 'Interview-focused template',
            template_type: 'episode',
            is_default: false,
            is_active: true
          }
        ];
        
        // Set default to first template
        episodeForm.value.template_id = availableTemplates.value[0].id;
        console.log('Using fallback templates, default selected:', availableTemplates.value[0]);
      } finally {
        loadingTemplates.value = false;
      }
    };

    const loadNextEpisodeNumber = async () => {
      loadingNextNumber.value = true;
      try {
        // Use the working next-number endpoint directly
        const response = await axios.get('/api/episodes/next-number');
        
        // The working endpoint returns {next_number: "0238"}
        const episodeNumber = response.data.next_number;
        episodeForm.value.episode_number = episodeNumber;
        
        // Calculate next Sunday for airdate
        const airDate = calculateNextSunday();
        episodeForm.value.airdate = airDate;
      } catch (error) {
        console.error('Failed to get next episode number:', error);
        // Final fallback
        episodeForm.value.episode_number = '0001';
        episodeForm.value.airdate = calculateNextSunday();
      } finally {
        loadingNextNumber.value = false;
      }
    };


    const calculateNextSunday = () => {
      const today = new Date();
      const nextSunday = new Date(today);
      nextSunday.setDate(today.getDate() + (7 - today.getDay()));
      return nextSunday.toISOString().split('T')[0];
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
        template_type: episode.template_type || 'sunday_show',
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
        console.log('Deleting episode:', episodeToDelete.value.episode_number);
        
        // Call backend delete API - this will remove from filesystem and database
        await axios.delete(`/api/episodes/${episodeToDelete.value.episode_number}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        
        console.log(`Episode ${episodeToDelete.value.episode_number} deleted successfully`);
        
        // Remove from local list
        const index = episodes.value.findIndex(ep => ep.episode_number === episodeToDelete.value.episode_number);
        if (index > -1) {
          episodes.value.splice(index, 1);
        }
        
        // Show success message
        alert(`Episode ${episodeToDelete.value.episode_number} has been permanently deleted from the filesystem and database.`);
        
        deleteDialog.value = false;
      } catch (error) {
        console.error('Failed to delete episode:', error);
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || error.message;
        alert(`Failed to delete episode: ${errorMessage}`);
      } finally {
        deleting.value = false;
        episodeToDelete.value = null;
      }
    };

    const closeEpisodeDialog = () => {
      episodeDialog.value = false;
      episodeForm.value = {
        episode_number: '',
        template_id: null,
        title: '',
        airdate: ''
      };
    };

    const saveEpisode = async () => {
      saving.value = true;
      try {
        if (editingEpisode.value) {
          // Update existing episode - send to info.md endpoint
          const updateData = {
            id: episodeForm.value.id,
            episode_number: episodeForm.value.episode_number,
            title: episodeForm.value.title || '',
            subtitle: episodeForm.value.subtitle || '',
            airdate: episodeForm.value.airdate || '',
            status: episodeForm.value.status || 'draft',
            duration: episodeForm.value.duration || '01:00:00',
            guest: episodeForm.value.guest || '',
            description: episodeForm.value.description || '',
            // Keep existing fields
            show_id: episodeForm.value.show_id,
            rundown_id: episodeForm.value.rundown_id,
            type: 'sunday_show',
            slug: `episode-${episodeForm.value.episode_number}`
          };
          
          await axios.put(`/api/episodes/${episodeForm.value.episode_number}/info`, updateData, {
            headers: { 
              'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
              'Content-Type': 'application/json'
            }
          });
          
          console.log(`Episode ${episodeForm.value.episode_number} updated successfully`);
          
        } else {
          // Create new episode using episode scaffolding API
          const createData = {
            episode_number: episodeForm.value.episode_number || undefined, // Let backend auto-generate if not provided
            template_id: episodeForm.value.template_id, // Use selected template
            title: episodeForm.value.title || null,
            episode_metadata: {
              airdate: episodeForm.value.airdate || '',
              status: 'draft',
              duration: '00:00:00',
              template_type: 'sunday_show'
            }
          };
          
          const response = await axios.post('/api/episodes/create', createData, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          
          // Redirect to content-editor on success
          if (response.data && response.data.episode_number) {
            router.push(`/content-editor/${response.data.episode_number}`);
            return;
          }
        }
        
        await fetchEpisodes();
        closeEpisodeDialog();
      } catch (error) {
        console.error('Failed to save episode:', error);
        // Show error message to user
        alert(`Failed to ${editingEpisode.value ? 'update' : 'create'} episode: ${error.response?.data?.detail || error.message}`);
      } finally {
        saving.value = false;
      }
    };

    // Production Tool Methods
    const calculateDuration = async (episode) => {
      // Set loading state
      episode.calculatingDuration = true;
      try {
        const response = await axios.post('/api/duration/calculate', {
          episode_number: episode.episode_number
        }, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        
        // Update episode duration in local state
        episode.duration = response.data.total_duration;
        console.log(`Duration calculated for episode ${episode.episode_number}: ${response.data.total_duration}`);
        
      } catch (error) {
        console.error('Failed to calculate duration:', error);
        alert(`Failed to calculate duration: ${error.response?.data?.detail || error.message}`);
      } finally {
        episode.calculatingDuration = false;
      }
    };

    const generateScript = async (episode) => {
      episode.generatingScript = true;
      try {
        const response = await axios.post('/api/script/generate', {
          episode_number: episode.episode_number,
          script_type: 'host'
        }, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        
        // Download the script
        const blob = new Blob([response.data.script_content], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `episode_${episode.episode_number}_host_script.html`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log(`Script generated for episode ${episode.episode_number}`);
        
      } catch (error) {
        console.error('Failed to generate script:', error);
        alert(`Failed to generate script: ${error.response?.data?.detail || error.message}`);
      } finally {
        episode.generatingScript = false;
      }
    };

    const collectMedia = async (episode) => {
      episode.collectingMedia = true;
      try {
        const response = await axios.post('/api/media/collect', {
          episode_number: episode.episode_number
        }, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        
        alert(`Media collection completed for episode ${episode.episode_number}. ${response.data.files_collected} files collected to ${response.data.output_path}`);
        console.log(`Media collected for episode ${episode.episode_number}:`, response.data);
        
      } catch (error) {
        console.error('Failed to collect media:', error);
        alert(`Failed to collect media: ${error.response?.data?.detail || error.message}`);
      } finally {
        episode.collectingMedia = false;
      }
    };

    // Lifecycle
    onMounted(async () => {
      // Load color system and episodes in parallel
      await Promise.all([
        loadColorsFromDatabase('default'),
        fetchEpisodes()
      ]);
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
      templateOptions,
      availableTemplates,
      loadingTemplates,
      loadingNextNumber,
      filteredEpisodes,
      fetchEpisodes,
      formatDate,
      isUpcoming,
      getStatusColor,
      formatEpisodeNumber,
      createNewEpisode,
      editEpisode,
      openRundown,
      duplicateEpisode,
      deleteEpisode,
      confirmDelete,
      closeEpisodeDialog,
      saveEpisode,
      loadNextEpisodeNumber,
      // Production tools
      calculateDuration,
      generateScript,
      collectMedia
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

/* Fix label positioning in episode form */
.episode-form .v-field-label {
  transform: translateY(-50%);
  top: 16px;
  position: absolute;
  left: 16px;
  pointer-events: none;
  transition: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  transition-property: all;
  max-width: calc(100% - 32px);
}

.episode-form .v-field--focused .v-field-label,
.episode-form .v-field--active .v-field-label {
  transform: translateY(-50%) translateX(-2px) scale(0.75);
  top: 0;
  left: 16px;
  max-width: calc(133.333333% - 32px);
  background: white;
  padding: 0 4px;
  z-index: 1;
}

/* Ensure proper positioning for outlined fields */
.episode-form .v-field--variant-outlined .v-field-label {
  top: 16px;
}

.episode-form .v-field--variant-outlined.v-field--focused .v-field-label,
.episode-form .v-field--variant-outlined.v-field--active .v-field-label {
  top: 0;
  background: white;
  padding: 0 4px;
}

/* Fix for when field has value */
.episode-form .v-field--dirty .v-field-label {
  transform: translateY(-50%) translateX(-2px) scale(0.75);
  top: 0;
  left: 16px;
  background: white;
  padding: 0 4px;
}

/* Full cell chip styling - target the specific table cells */
.v-data-table .v-data-table__td {
  position: relative;
  vertical-align: middle;
}

/* Override default Vuetify table cell padding for chip columns */
.v-data-table .v-data-table__td:has(.full-cell-chip) {
  padding: 0 !important;
}

/* Make chips completely fill their cells */
.v-data-table .full-cell-chip {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 8px !important;
  border-radius: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: auto !important;
}

/* Override Vuetify chip specific styles */
.full-cell-chip .v-chip__content {
  padding: 0 !important;
  font-weight: 500 !important;
}

/* Override Vuetify's CSS variables for episode number chips */
.v-data-table .episode-number-chip.v-chip--size-small {
  --v-chip-size: 0.9375rem !important;  /* 15px - halfway between 12px and 18px */
  font-size: 0.9375rem !important;
  font-weight: 700 !important;
}

/* Target the content specifically too */
.v-data-table .episode-number-chip.v-chip .v-chip__content {
  font-size: 0.9375rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.5px !important;
}
</style>