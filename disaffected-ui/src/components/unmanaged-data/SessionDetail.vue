<template>
  <div>
    <!-- Session-level metadata strip -->
    <v-row dense class="mb-3">
      <v-col cols="12" md="3">
        <div class="text-caption text-grey">Session UUID</div>
        <div class="text-body-2" style="font-family: monospace; word-break: break-all;">
          {{ session.session_uuid }}
        </div>
      </v-col>
      <v-col cols="6" md="2">
        <div class="text-caption text-grey">Started</div>
        <div class="text-body-2">{{ formatWallclock(session.started_at) }}</div>
      </v-col>
      <v-col cols="6" md="2">
        <div class="text-caption text-grey">Ended</div>
        <div class="text-body-2">{{ formatWallclock(session.ended_at) || '—' }}</div>
      </v-col>
      <v-col cols="6" md="2">
        <div class="text-caption text-grey">vMix</div>
        <div class="text-body-2">{{ session.vmix_version || '—' }}</div>
      </v-col>
      <v-col cols="6" md="3">
        <div class="text-caption text-grey">Showtime</div>
        <div class="text-body-2">{{ session.showtime_version || '—' }}</div>
      </v-col>
    </v-row>

    <div v-if="session.recording_root_path" class="mb-3">
      <div class="text-caption text-grey">Recording root path</div>
      <div class="text-body-2" style="font-family: monospace;">
        {{ session.recording_root_path }}
      </div>
    </div>

    <div v-if="session.notes" class="mb-3">
      <div class="text-caption text-grey">Notes</div>
      <div class="text-body-2">{{ session.notes }}</div>
    </div>

    <v-divider class="mb-3" />

    <div class="text-subtitle-2 mb-2">
      Takes ({{ session.takes.length }})
    </div>

    <v-card
      v-if="session.takes.length === 0"
      flat
      class="pa-4 text-center text-grey text-caption"
      color="transparent"
    >
      No takes recorded.
    </v-card>

    <v-expansion-panels v-else variant="accordion" multiple>
      <v-expansion-panel
        v-for="take in session.takes"
        :key="take.id"
      >
        <v-expansion-panel-title>
          <div class="d-flex align-center flex-wrap" style="width: 100%; gap: 8px;">
            <v-chip size="x-small" :color="takeStatusColor(take.status)" variant="flat">
              {{ take.status }}
            </v-chip>
            <v-chip v-if="take.is_pickup" size="x-small" color="purple" variant="tonal">
              pickup
            </v-chip>
            <span
              class="text-body-2 font-weight-medium"
              style="font-family: monospace;"
            >
              {{ take.filename }}
            </span>
            <v-spacer />
            <span class="text-caption text-grey">
              {{ take.duration_seconds != null ? formatDuration(take.duration_seconds) : '—' }}
            </span>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-row dense>
            <v-col cols="6" md="3">
              <div class="text-caption text-grey">Started</div>
              <div class="text-body-2">{{ formatWallclock(take.started_at_wallclock) }}</div>
            </v-col>
            <v-col cols="6" md="3">
              <div class="text-caption text-grey">Ended</div>
              <div class="text-body-2">{{ formatWallclock(take.ended_at_wallclock) || '—' }}</div>
            </v-col>
            <v-col cols="6" md="2">
              <div class="text-caption text-grey">Category</div>
              <div class="text-body-2">{{ take.category || '—' }}</div>
            </v-col>
            <v-col cols="6" md="2">
              <div class="text-caption text-grey">Block</div>
              <div class="text-body-2">{{ take.block_letter || '—' }}</div>
            </v-col>
            <v-col cols="6" md="2">
              <div class="text-caption text-grey">Seg / Take / Pickup</div>
              <div class="text-body-2">
                {{ take.segment_number ?? '—' }} /
                {{ take.take_number ?? '—' }} /
                {{ take.pickup_number ?? '—' }}
              </div>
            </v-col>
          </v-row>

          <!-- Pickup metadata -->
          <v-card
            v-if="take.is_pickup"
            flat
            class="pa-3 mt-3"
            color="purple-lighten-5"
          >
            <div class="text-subtitle-2 mb-1">Pickup splice info</div>
            <v-row dense>
              <v-col cols="12" md="4">
                <div class="text-caption text-grey">Replaces from</div>
                <div class="text-body-2">{{ take.pickup_replaces_from_seconds }}s</div>
              </v-col>
              <v-col cols="12" md="4">
                <div class="text-caption text-grey">Back seconds</div>
                <div class="text-body-2">{{ take.pickup_back_seconds }}</div>
              </v-col>
              <v-col cols="12" md="4">
                <div class="text-caption text-grey">Splices into</div>
                <div class="text-body-2" style="font-family: monospace;">
                  {{ take.pickup_splices_into_filename || '—' }}
                </div>
              </v-col>
            </v-row>
          </v-card>

          <div v-if="take.operator_note" class="mt-3">
            <div class="text-caption text-grey">Operator note</div>
            <div class="text-body-2">{{ take.operator_note }}</div>
          </div>

          <!-- Markers -->
          <div v-if="take.markers?.length > 0" class="mt-3">
            <div class="text-subtitle-2 mb-1">Markers ({{ take.markers.length }})</div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Offset</th>
                  <th>Kind</th>
                  <th>Wallclock</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in take.markers" :key="m.id">
                  <td>{{ m.offset_seconds }}s</td>
                  <td>
                    <v-chip size="x-small" :color="markerKindColor(m.kind)" variant="tonal">
                      {{ m.kind }}
                    </v-chip>
                  </td>
                  <td>{{ formatWallclock(m.wallclock) }}</td>
                  <td>{{ m.note || '' }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>

          <!-- Cue fires -->
          <div v-if="take.cue_fires?.length > 0" class="mt-3">
            <div class="text-subtitle-2 mb-1">Cue fires ({{ take.cue_fires.length }})</div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Fired at</th>
                  <th>Type</th>
                  <th>Title</th>
                  <th>Trigger</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in take.cue_fires" :key="c.id">
                  <td>{{ formatWallclock(c.fired_at_wallclock) }}</td>
                  <td>
                    <v-chip size="x-small" variant="tonal">
                      {{ c.cue_type || '—' }}
                    </v-chip>
                  </td>
                  <td>{{ c.cue_title || '—' }}</td>
                  <td>{{ c.trigger || '—' }}</td>
                  <td>{{ c.status }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup>
defineProps({
  session: {
    type: Object,
    required: true,
  },
})

function formatWallclock(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function formatDuration(seconds) {
  if (seconds == null) return ''
  const total = Math.round(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function takeStatusColor(status) {
  switch (status) {
    case 'good': return 'green'
    case 'discard': return 'red'
    case 'reshoot': return 'orange-darken-2'
    case 'pickup-target': return 'purple-darken-1'
    case 'pending_review':
    default: return 'grey'
  }
}

function markerKindColor(kind) {
  switch (kind) {
    case 'good': return 'green'
    case 'bad': return 'red'
    case 'pickup': return 'purple-darken-1'
    case 'flag': return 'orange-darken-2'
    case 'cut': return 'red-darken-1'
    case 'note':
    default: return 'grey'
  }
}
</script>
