<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-6">Voice Meeting</h2>
        <p class="text-subtitle-1">Audio conference brainstorming with recording</p>
      </v-col>
    </v-row>

    <!-- Active Conference Display -->
    <v-row v-if="activeConference" justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon color="error" class="mr-2">mdi-record-circle</v-icon>
            Active Conference: {{ activeConference.title }}
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-list density="compact">
                  <v-list-item>
                    <v-list-item-title>Conference ID</v-list-item-title>
                    <v-list-item-subtitle>{{ activeConference.conference_id }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>PIN</v-list-item-title>
                    <v-list-item-subtitle class="text-h6 font-weight-bold">{{ activeConference.pin }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Dial-In Number</v-list-item-title>
                    <v-list-item-subtitle>{{ activeConference.dial_in_number }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Recording</v-list-item-title>
                    <v-list-item-subtitle>
                      <v-chip size="small" color="error">
                        <v-icon left size="small">mdi-record</v-icon>
                        Recording
                      </v-chip>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="6">
                <v-btn
                  v-if="!isConnected"
                  color="primary"
                  size="large"
                  block
                  class="mb-2"
                  @click="joinFromBrowser"
                  :loading="joiningConference"
                >
                  <v-icon left>mdi-phone</v-icon>
                  Join from Browser (WebRTC)
                </v-btn>

                <!-- WebRTC Controls (shown when connected) -->
                <div v-if="isConnected" class="mb-2">
                  <v-chip color="success" class="mb-3" block>
                    <v-icon left>mdi-phone-in-talk</v-icon>
                    Connected
                  </v-chip>
                  <v-row dense>
                    <v-col cols="6">
                      <v-btn
                        :color="isMuted ? 'error' : 'primary'"
                        block
                        @click="toggleMute"
                      >
                        <v-icon left>{{ isMuted ? 'mdi-microphone-off' : 'mdi-microphone' }}</v-icon>
                        {{ isMuted ? 'Unmute' : 'Mute' }}
                      </v-btn>
                    </v-col>
                    <v-col cols="6">
                      <v-btn
                        color="error"
                        block
                        @click="hangup"
                      >
                        <v-icon left>mdi-phone-hangup</v-icon>
                        Leave
                      </v-btn>
                    </v-col>
                  </v-row>
                </div>

                <v-btn
                  color="error"
                  variant="outlined"
                  block
                  @click="endConference"
                  :loading="endingConference"
                >
                  <v-icon left>mdi-phone-hangup</v-icon>
                  End Conference
                </v-btn>
              </v-col>
            </v-row>

            <!-- Audio Level Meters -->
            <v-divider class="my-4"></v-divider>
            <LEDMeter />

            <!-- Participants List -->
            <v-divider class="my-4"></v-divider>
            <h3 class="text-h6 mb-2">Participants ({{ participants.length }})</h3>
            <v-list density="compact">
              <v-list-item
                v-for="participant in participants"
                :key="participant.participant_id"
              >
                <template v-slot:prepend>
                  <v-icon :color="participant.name ? 'success' : 'warning'">
                    {{ participant.join_method === 'webrtc' ? 'mdi-laptop' : 'mdi-phone' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ participant.name || 'Unknown' }}
                  <v-chip size="x-small" v-if="!participant.name" color="warning" class="ml-2">Unidentified</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ participant.caller_id }} • Joined {{ formatTime(participant.joined_at) }}
                </v-list-item-subtitle>
                <template v-slot:append v-if="!participant.name">
                  <v-btn
                    size="small"
                    color="primary"
                    variant="text"
                    @click="openIdentifyDialog(participant)"
                  >
                    Identify
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Conference Form -->
    <v-row v-else justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card>
          <v-card-title>Start New Conference</v-card-title>
          <v-card-text>
            <v-form ref="conferenceFormRef" @submit.prevent="createConference">
              <v-row>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="newConference.episodeId"
                    :items="episodeOptions"
                    label="Episode"
                    item-title="label"
                    item-value="value"
                    placeholder="Select episode for this conference"
                    required
                    :rules="[v => !!v || 'Episode is required']"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="newConference.title"
                    label="Conference Title"
                    placeholder="e.g., Interview with Dr. Jane Doe"
                  />
                </v-col>
              </v-row>
              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="creatingConference"
                :disabled="!newConference.episodeId"
              >
                <v-icon left>mdi-phone-plus</v-icon>
                Start Conference
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row v-if="!activeConference" justify="center" class="mt-4">
      <v-col cols="12" md="10" lg="8">
        <v-card>
          <v-card-title class="text-subtitle-1">How It Works</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-numeric-1-circle</v-icon>
                </template>
                <v-list-item-title>Start conference</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-numeric-2-circle</v-icon>
                </template>
                <v-list-item-title>Share dial-in number and PIN</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-numeric-3-circle</v-icon>
                </template>
                <v-list-item-title>Participants state their names</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-numeric-4-circle</v-icon>
                </template>
                <v-list-item-title>Brainstorm and record</v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-numeric-5-circle</v-icon>
                </template>
                <v-list-item-title>End for transcription</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Conferences List -->
    <v-row justify="center" class="mt-4">
      <v-col cols="12" md="10" lg="8">
        <v-card>
          <v-card-title>Recent Conferences</v-card-title>
          <v-card-text>
            <v-list v-if="recentConferences.length > 0" density="compact">
              <v-list-item
                v-for="conf in recentConferences"
                :key="conf.conference_id"
              >
                <v-list-item-title>{{ conf.title }}</v-list-item-title>
                <v-list-item-subtitle>
                  Episode {{ conf.episode_id }} • {{ conf.participant_count }} participants • {{ formatTime(conf.created_at) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <v-alert v-else type="info" variant="text">
              No recent conferences
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Identify Participant Dialog -->
    <v-dialog v-model="identifyDialog" max-width="500">
      <v-card>
        <v-card-title>Identify Participant</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="identifyForm.name"
            label="Participant Name"
            placeholder="e.g., Dr. Jane Doe"
            autofocus
            @keyup.enter="identifyParticipant"
          />
          <p class="text-caption">
            Caller ID: {{ identifyForm.caller_id }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="identifyDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="identifyParticipant"
            :loading="identifyingParticipant"
            :disabled="!identifyForm.name"
          >
            Identify
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import axios from 'axios'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import LEDMeter from '@/components/LEDMeter.vue' // eslint-disable-line no-unused-vars
import { UserAgent, Inviter, SessionState } from 'sip.js'

// State
const activeConference = ref(null)
const participants = ref([])
const recentConferences = ref([])
const episodeOptions = ref([])
const conferenceFormRef = ref(null) // eslint-disable-line no-unused-vars

// Form data
const newConference = ref({
  episodeId: null,
  title: ''
})

// Loading states
const creatingConference = ref(false)
const endingConference = ref(false)
const joiningConference = ref(false)
const identifyingParticipant = ref(false)

// WebRTC state
const userAgent = ref(null)
const session = ref(null)
const isConnected = ref(false)
const isMuted = ref(false)

// Identify dialog
const identifyDialog = ref(false)
const identifyForm = ref({
  participant_id: null,
  name: '',
  caller_id: ''
})

// Snackbar
const snackbar = ref({
  show: false,
  message: '',
  color: 'info'
})

// Methods
const showSnackbar = (message, color = 'info') => {
  snackbar.value = {
    show: true,
    message,
    color
  }
}

const loadEpisodes = async () => {
  try {
    const response = await axios.get('/episodes', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.data.episodes) {
      episodeOptions.value = response.data.episodes.map(ep => ({
        label: `Episode ${ep.episode_number} - ${ep.title}`,
        value: ep.episode_number
      }))
    }
  } catch (error) {
    console.error('Failed to load episodes:', error)
    showSnackbar('Failed to load episodes', 'error')
  }
}

const loadActiveConferences = async () => {
  try {
    const response = await axios.get('/api/voice/conference/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.data.success && response.data.conferences.length > 0) {
      // Load details of first active conference
      const conf = response.data.conferences[0]
      await loadConferenceDetails(conf.conference_id)
    }
  } catch (error) {
    console.error('Failed to load active conferences:', error)
  }
}

const loadConferenceDetails = async (conferenceId) => {
  try {
    const response = await axios.get(`/api/voice/conference/${conferenceId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.data.success) {
      activeConference.value = response.data.conference
      participants.value = response.data.conference.participants || []
    }
  } catch (error) {
    console.error('Failed to load conference details:', error)
  }
}

const loadRecentConferences = async () => {
  try {
    const response = await axios.get('/api/voice/conference/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.data.success) {
      recentConferences.value = response.data.conferences
    }
  } catch (error) {
    console.error('Failed to load recent conferences:', error)
  }
}

const createConference = async () => {
  if (!newConference.value.episodeId) {
    showSnackbar('Please select an episode', 'warning')
    return
  }

  creatingConference.value = true
  try {
    const response = await axios.post('/api/voice/conference/create', {
      episode_id: newConference.value.episodeId,
      title: newConference.value.title || null
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
        'Content-Type': 'application/json'
      }
    })

    if (response.data.success) {
      activeConference.value = response.data.conference
      participants.value = []
      showSnackbar('Conference created successfully', 'success')

      // Reset form
      newConference.value = {
        episodeId: null,
        title: ''
      }
    }
  } catch (error) {
    console.error('Failed to create conference:', error)
    showSnackbar(error.response?.data?.detail || 'Failed to create conference', 'error')
  } finally {
    creatingConference.value = false
  }
}

const joinFromBrowser = async () => {
  if (!activeConference.value) return

  joiningConference.value = true
  try {
    const response = await axios.post(
      `/api/voice/conference/${activeConference.value.conference_id}/join`,
      { join_method: 'webrtc' },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      showSnackbar('Connecting to conference...', 'info')

      // Initialize WebRTC SIP client
      const config = response.data.webrtc_config
      // Use proxy path - Vue dev server will forward to Asterisk ws://192.168.51.223:8088/ws
      const server = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/asterisk-ws`
      const conferenceUri = `sip:${activeConference.value.conference_id}@192.168.51.223`

      // Create SIP.js UserAgent
      const uri = UserAgent.makeURI(`sip:${config.username}@192.168.51.223`)
      userAgent.value = new UserAgent({
        uri: uri,
        transportOptions: {
          server: server
        },
        authorizationUsername: config.username,
        authorizationPassword: '',
        displayName: config.display_name || 'Show-Build User',
        sessionDescriptionHandlerFactoryOptions: {
          constraints: {
            audio: true,
            video: false
          }
        }
      })

      // Start the UserAgent
      await userAgent.value.start()

      // Create outgoing call to conference
      const target = UserAgent.makeURI(conferenceUri)
      const inviter = new Inviter(userAgent.value, target)
      session.value = inviter

      // Setup session state change handler
      inviter.stateChange.addListener((state) => {
        console.log('Session state:', state)
        switch (state) {
          case SessionState.Established:
            isConnected.value = true
            showSnackbar('Connected to conference', 'success')
            // Setup remote audio
            setupRemoteAudio(inviter)
            break
          case SessionState.Terminated:
            isConnected.value = false
            showSnackbar('Disconnected from conference', 'info')
            cleanup()
            break
        }
      })

      // Send INVITE
      await inviter.invite()

      // Reload participants
      await loadConferenceDetails(activeConference.value.conference_id)
    }
  } catch (error) {
    console.error('Failed to join conference:', error)
    showSnackbar(error.response?.data?.detail || 'Failed to join conference', 'error')
    cleanup()
  } finally {
    joiningConference.value = false
  }
}

const setupRemoteAudio = (sessionObj) => {
  const remoteStream = new MediaStream()
  const pc = sessionObj.sessionDescriptionHandler.peerConnection

  pc.getReceivers().forEach((receiver) => {
    if (receiver.track) {
      remoteStream.addTrack(receiver.track)
    }
  })

  // Create audio element for remote audio
  const audioElement = new Audio()
  audioElement.srcObject = remoteStream
  audioElement.play().catch(e => console.error('Audio play failed:', e))
}

const toggleMute = () => {
  if (!session.value) return

  const pc = session.value.sessionDescriptionHandler.peerConnection
  const senders = pc.getSenders()

  senders.forEach((sender) => {
    if (sender.track && sender.track.kind === 'audio') {
      sender.track.enabled = !sender.track.enabled
      isMuted.value = !sender.track.enabled
    }
  })

  showSnackbar(isMuted.value ? 'Microphone muted' : 'Microphone unmuted', 'info')
}

const hangup = async () => {
  if (!session.value) return

  try {
    await session.value.bye()
    cleanup()
    showSnackbar('Left conference', 'info')
  } catch (error) {
    console.error('Hangup error:', error)
    cleanup()
  }
}

const cleanup = () => {
  if (userAgent.value) {
    userAgent.value.stop()
    userAgent.value = null
  }
  session.value = null
  isConnected.value = false
  isMuted.value = false
}

const endConference = async () => {
  if (!activeConference.value) return

  if (!confirm('Are you sure you want to end this conference? Recording will be processed for transcription.')) {
    return
  }

  endingConference.value = true
  try {
    const response = await axios.post(
      `/api/voice/conference/${activeConference.value.conference_id}/end`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
        }
      }
    )

    if (response.data.success) {
      showSnackbar('Conference ended. Recording will be transcribed.', 'success')
      activeConference.value = null
      participants.value = []
      await loadRecentConferences()
    }
  } catch (error) {
    console.error('Failed to end conference:', error)
    showSnackbar(error.response?.data?.detail || 'Failed to end conference', 'error')
  } finally {
    endingConference.value = false
  }
}

const openIdentifyDialog = (participant) => {
  identifyForm.value = {
    participant_id: participant.participant_id,
    name: '',
    caller_id: participant.caller_id
  }
  identifyDialog.value = true
}

const identifyParticipant = async () => {
  if (!identifyForm.value.name || !activeConference.value) return

  identifyingParticipant.value = true
  try {
    const response = await axios.post(
      `/api/voice/conference/${activeConference.value.conference_id}/identify`,
      {
        participant_id: identifyForm.value.participant_id,
        name: identifyForm.value.name
      },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
          'Content-Type': 'application/json'
        }
      }
    )

    if (response.data.success) {
      showSnackbar('Participant identified successfully', 'success')
      identifyDialog.value = false
      await loadConferenceDetails(activeConference.value.conference_id)
    }
  } catch (error) {
    console.error('Failed to identify participant:', error)
    showSnackbar(error.response?.data?.detail || 'Failed to identify participant', 'error')
  } finally {
    identifyingParticipant.value = false
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// Lifecycle
onMounted(async () => {
  await loadEpisodes()
  await loadActiveConferences()
  await loadRecentConferences()
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.v-list-item-title {
  font-weight: 500;
}
</style>
