<template>
  <v-card flat>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-server-network</v-icon>
      Celery Workers
      <v-spacer />
      <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="loadAll">
        Refresh
      </v-btn>
      <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="openNew">
        Define Worker
      </v-btn>
    </v-card-title>

    <v-card-subtitle>
      Declarative worker fleet — name + image/repo URL, host, queues, flavor.
      Stores definitions and shows live status; it does not deploy.
    </v-card-subtitle>

    <v-card-text>
      <v-alert v-if="statusError" type="warning" variant="tonal" density="compact" class="mb-3">
        Live status unavailable: {{ statusError }}
      </v-alert>

      <v-table density="comfortable">
        <thead>
          <tr>
            <th>Status</th>
            <th>Name</th>
            <th>Image / Repo</th>
            <th>Flavor</th>
            <th>Host</th>
            <th>Queues</th>
            <th>Conc.</th>
            <th>GPU</th>
            <th>Enabled</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in workers" :key="w.id">
            <td>
              <v-tooltip :text="w.online ? ('online: ' + (w.live_node || '')) : 'offline'">
                <template #activator="{ props }">
                  <v-icon v-bind="props" :color="w.online ? 'success' : 'grey'" size="small">
                    {{ w.online ? 'mdi-circle' : 'mdi-circle-outline' }}
                  </v-icon>
                </template>
              </v-tooltip>
            </td>
            <td class="font-weight-medium">{{ w.name }}</td>
            <td class="text-truncate" style="max-width: 280px">
              <code class="text-caption">{{ w.image }}</code>
            </td>
            <td><v-chip v-if="w.flavor" size="x-small" :color="flavorColor(w.flavor)">{{ w.flavor }}</v-chip></td>
            <td>{{ w.host || '—' }}</td>
            <td>
              <v-chip v-for="q in (w.queues || [])" :key="q" size="x-small" class="mr-1 mb-1">{{ q }}</v-chip>
            </td>
            <td>{{ w.concurrency }}</td>
            <td>{{ w.gpu || '—' }}</td>
            <td>
              <v-switch
                :model-value="w.enabled" color="primary" density="compact" hide-details
                @update:model-value="toggleEnabled(w, $event)" />
            </td>
            <td class="text-right">
              <v-btn icon="mdi-pencil" size="x-small" variant="text" @click="openEdit(w)" />
              <v-btn icon="mdi-delete" size="x-small" variant="text" color="error" @click="removeWorker(w)" />
            </td>
          </tr>
          <tr v-if="!workers.length">
            <td colspan="10" class="text-center text-medium-emphasis py-6">
              No workers defined yet. Click “Define Worker” to add one.
            </td>
          </tr>
        </tbody>
      </v-table>

      <!-- Online-but-undefined workers (discovered from Celery, not in the table) -->
      <div v-if="undefinedOnline.length" class="mt-4">
        <div class="text-caption text-medium-emphasis mb-1">
          Live workers not yet defined here:
        </div>
        <v-chip v-for="n in undefinedOnline" :key="n.node" size="small" class="mr-2 mb-1"
                prepend-icon="mdi-circle" color="success" variant="tonal">
          {{ n.node }} ({{ (n.queues || []).join(', ') }})
        </v-chip>
      </div>
    </v-card-text>

    <!-- Create / edit dialog -->
    <v-dialog v-model="dialog" max-width="640">
      <v-card>
        <v-card-title>{{ editing.id ? 'Edit Worker' : 'Define Worker' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="editing.name" label="Name *" density="compact"
            hint="Worker name (matches celery --hostname name part, e.g. media)" persistent-hint />
          <v-text-field v-model="editing.image" label="Image / Repo URL *" density="compact" class="mt-2"
            hint="e.g. 192.168.51.206:3000/showbuild/worker-media-gpu:latest" persistent-hint />
          <v-select v-model="editing.flavor" :items="['base','media-cpu','media-gpu']"
            label="Flavor" density="compact" clearable class="mt-2" />
          <v-text-field v-model="editing.host" label="Host" density="compact" class="mt-2"
            hint="prefect / kairo / proxima / whisperbox" persistent-hint />
          <v-combobox v-model="editing.queues" label="Queues" multiple chips clearable
            density="compact" class="mt-2"
            hint="e.g. media, assets, assets_low" persistent-hint />
          <div class="d-flex gap-4 mt-2">
            <v-text-field v-model.number="editing.concurrency" label="Concurrency" type="number"
              density="compact" style="max-width: 140px" />
            <v-text-field v-model="editing.gpu" label="GPU" density="compact"
              hint="all = --gpus all; blank = none" persistent-hint style="max-width: 200px" />
            <v-text-field v-model="editing.owner_tool" label="Owner tool" density="compact"
              style="max-width: 200px" />
          </div>
          <v-textarea v-model="editing.notes" label="Notes" rows="2" density="compact" class="mt-2" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!editing.name || !editing.image" @click="save">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script>
import { api } from '@/utils/apiHelpers'

export default {
  name: 'WorkerSettings',
  data () {
    return {
      workers: [],
      onlineNodes: [],
      statusError: null,
      dialog: false,
      saving: false,
      editing: this.blank(),
    }
  },
  computed: {
    undefinedOnline () {
      const definedNames = new Set(this.workers.map(w => w.name))
      return this.onlineNodes.filter(n => !definedNames.has((n.node || '').split('@')[0]))
    },
  },
  mounted () {
    this.loadAll()
  },
  methods: {
    blank () {
      return {
        id: null, name: '', image: '', flavor: null, host: '',
        queues: [], concurrency: 1, gpu: '', owner_tool: '', notes: '', enabled: true,
      }
    },
    flavorColor (f) {
      return { base: 'blue-grey', 'media-cpu': 'teal', 'media-gpu': 'deep-purple' }[f] || 'grey'
    },
    async loadAll () {
      try {
        const data = await api('/settings/workers/status')
        this.workers = data.defined || []
        this.onlineNodes = data.online || []
        this.statusError = data.error || null
      } catch (e) {
        // fall back to plain list if status probe fails entirely
        this.statusError = String(e)
        try {
          this.workers = await api('/settings/workers')
        } catch (_) { /* noop */ }
      }
    },
    openNew () { this.editing = this.blank(); this.dialog = true },
    openEdit (w) { this.editing = { ...w, queues: [...(w.queues || [])] }; this.dialog = true },
    async save () {
      this.saving = true
      try {
        const body = {
          name: this.editing.name,
          image: this.editing.image,
          flavor: this.editing.flavor || null,
          host: this.editing.host || null,
          queues: this.editing.queues || [],
          concurrency: Number(this.editing.concurrency) || 1,
          gpu: this.editing.gpu || null,
          owner_tool: this.editing.owner_tool || null,
          notes: this.editing.notes || null,
          enabled: this.editing.enabled !== false,
        }
        if (this.editing.id) {
          await api(`/settings/workers/${this.editing.id}`, { method: 'PATCH', body: JSON.stringify(body) })
        } else {
          await api('/settings/workers', { method: 'POST', body: JSON.stringify(body) })
        }
        this.dialog = false
        await this.loadAll()
      } catch (e) {
        this.statusError = 'Save failed: ' + String(e)
      } finally {
        this.saving = false
      }
    },
    async toggleEnabled (w, val) {
      await api(`/settings/workers/${w.id}`, { method: 'PATCH', body: JSON.stringify({ enabled: val }) })
      await this.loadAll()
    },
    async removeWorker (w) {
      if (!confirm(`Delete worker "${w.name}"? (does not stop a running worker)`)) return
      await api(`/settings/workers/${w.id}`, { method: 'DELETE' })
      await this.loadAll()
    },
  },
}
</script>
