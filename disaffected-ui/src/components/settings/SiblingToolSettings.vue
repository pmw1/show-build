<template>
  <v-card flat>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-hub</v-icon>
      Sibling Tools
      <v-spacer />
      <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="load">Refresh</v-btn>
    </v-card-title>
    <v-card-subtitle>
      Where the sibling production tools live. Show-Build is the hub; these point it
      at showtime (recording), media-prep (conversion), and media-distribute (promotion).
    </v-card-subtitle>

    <v-card-text>
      <v-row>
        <v-col v-for="t in tools" :key="t.tool" cols="12" md="4">
          <v-card variant="outlined">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <v-icon start size="small">{{ toolIcon(t.tool) }}</v-icon>
              {{ t.tool }}
              <v-spacer />
              <v-icon v-if="health[t.tool]" :color="health[t.tool].reachable ? 'success' : 'error'" size="small">
                {{ health[t.tool].reachable ? 'mdi-check-circle' : 'mdi-alert-circle' }}
              </v-icon>
            </v-card-title>
            <v-card-text>
              <v-text-field
                v-model="t.base_url" label="Base URL" density="compact"
                placeholder="https://host:port" hide-details class="mb-3" />
              <div class="d-flex align-center">
                <v-switch v-model="t.enabled" label="Enabled" color="primary" density="compact" hide-details />
                <v-spacer />
                <v-btn size="x-small" variant="text" :loading="probing === t.tool" @click="probe(t)">
                  Test
                </v-btn>
              </div>
              <div v-if="health[t.tool]" class="text-caption mt-1"
                   :class="health[t.tool].reachable ? 'text-success' : 'text-error'">
                {{ health[t.tool].reachable
                    ? ('reachable (' + (health[t.tool].status_code || '') + ' ' + (health[t.tool].probe || '') + ')')
                    : ('unreachable: ' + (health[t.tool].detail || '')) }}
              </div>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn size="small" color="primary" variant="tonal" :loading="saving === t.tool" @click="save(t)">
                Save
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
import { api } from '@/utils/apiHelpers'

export default {
  name: 'SiblingToolSettings',
  data () {
    return { tools: [], health: {}, saving: null, probing: null }
  },
  mounted () { this.load() },
  methods: {
    toolIcon (t) {
      return {
        showtime: 'mdi-record-circle',
        'media-prep': 'mdi-cog-transfer',
        'media-distribute': 'mdi-share-variant',
      }[t] || 'mdi-tools'
    },
    async load () {
      try {
        this.tools = await api('/settings/tools')
      } catch (e) { this.tools = [] }
    },
    async save (t) {
      this.saving = t.tool
      try {
        await api(`/settings/tools/${t.tool}`, {
          method: 'PUT',
          body: JSON.stringify({ base_url: t.base_url || null, enabled: t.enabled !== false }),
        })
        await this.probe(t)
      } finally {
        this.saving = null
      }
    },
    async probe (t) {
      this.probing = t.tool
      try {
        const h = await api(`/settings/tools/${t.tool}/health`)
        this.health = { ...this.health, [t.tool]: h }
      } catch (e) {
        this.health = { ...this.health, [t.tool]: { reachable: false, detail: String(e) } }
      } finally {
        this.probing = null
      }
    },
  },
}
</script>
